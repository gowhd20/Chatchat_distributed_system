import random, string, uuid
import pickle
import hashlib
import base64
import logging
import json
import os
import OpenSSL

import calendar, datetime, time
import pytz
from datetime import timedelta

from pytz import timezone
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_v1_5, PKCS1_OAEP
from logging import getLogger


_ACTION_KEYS = ('server_info', 'new_node_joined', 'remove_inactive_node', 
    'refresh_common_key', 'aquired_access_to_res', 'add_new_comment', 
    'access_close', 'request_availability', 'access_permitted')

MAX_TRY = 3
EXCHANGE_FOR_ALL = "to_all_nodes"
EXCHANGE_FOR_THIRDPARTY = "to_all_master_nodes"
EXCHANGE_END_TO_END = "end_to_end"
MN_RKEY = "channel_to_masterserver"
TIMER_INS = "timer_instance"
TOPIC_NEW_NODE = "topic_new_node"
TOPIC_MASTER_NODES = "only_master_nodes"


RES_HOLDER = "accessed_by"
FAILED_NODES = "failed_nodes"

## slave node
CHECK_HEARTBEAT = 5
_TIMEOUT = 10
REDIS_ID_NODE = 10


## master node
REDIS_ID = 0
COMMON_KEY_TIMEOUT = 60
INSPECTION_TIME_INTERVAL = 6
TIME_DETERMINE_INACTIVE = 13     ## 5 sec => test purpose\
TIME_DETERMINE_USER_ACTIVE = 60
CLEAN_GARBAGE_NODES = 60*60

PORT = 1327
HOST_ADDR = "192.168.10.102"
ID_OF_MN = 0
SESSION_EXTENDED_BY = 30


## Advanced Encryption Standard
## encrypt text with aes, generate iv and wrap altogether in json format with nonce from cipher
## nonce is going to be used when decrypt aes
## cipher generates nonce and encrypts message with iv

## [BEGIN] private apis
## encrypt plain text by AES
## symetric key cryptography 
## key == session key/symmetric key, discarded every time it finishes the execution
## iv == initialization vectors that it makes ciphertext unpredictable even under same content of text.
## Also known as nonce(number used once). These are open to wild when transfer 

## To make things perfectly secure, we need to authenticate IV and ciphertext with different keys
## Two different keys are required one for encryption and the other for MAC
## More details take a look into CBC-MAC
def _encrypt_aes(raw_txt):
    ## hash keeps integrity of data, not to be changed
    ## hash alias : message digest, checksum
    ## encoding raw content is required if later it has to be compared with newly created hash by same input
    key = hashlib.sha256(get_random_bytes(AES.block_size)).digest() # => a 32 byte string
    padded_txt = _padding(raw_txt)
    iv = Random.new().read(AES.block_size)   ## iv == nonce
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # encode ciphertext for the purpose of the data to be properly consumed
    # https://danielmiessler.com/study/encoding-encryption-hashing-obfuscation/
    return {'key': key, 'iv': iv, 'cipher_txt': base64.b64encode(cipher.encrypt(padded_txt))}  


## asymetric key cryptography
# encrypt key(symmetric key/AES) with receiver's public_key
def _encrypt_rsa(public_key, key):
    if type(public_key) is unicode:
        public_key = RSA.importKey(public_key)
    cipher_rsa = PKCS1_OAEP.new(public_key)
    return cipher_rsa.encrypt(key)


## Is needed as the size of message differs each time
def _padding(txt):
    return txt+(AES.block_size-len(txt)%AES.block_size)*chr(AES.block_size-len(txt)%AES.block_size)


# decrypt text using key from aes algorithm
def _decrypt_aes(key, iv, cipher_txt):
    cipher_txt = base64.b64decode(cipher_txt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return _unpadding(cipher.decrypt(cipher_txt).decode('utf-8'))


## Rivest, Shamir, Adleman
## decrypt symetric key(AES) with private key(RSA)
## decrypt iv encrypted by sender's public key to decrypt message content was encrypted with aes
def _decrypt_rsa(private_key, secured_key):
    if type(private_key) is unicode:
        private_key = RSA.importKey(private_key)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    ## added for using PKCS1_v1_5, not needed when using PKCS1_OAEP
    #dsize = SHA.digest_size
    #sentinel = Random.new().read(AES.block_size+dsize)         # Let's assume that average data length is 16
    ## ------------------
    return cipher_rsa.decrypt(secured_key)


def _unpadding(txt):
    return txt[:-ord(txt[len(txt)-1:])]


## [BEGIN] public apis
## encrypt message between clients and web server
def encrypt_msg(public_key, message):
    if not isinstance(message, str):
        message = json.dumps(message)
        
    aes_encrypted_data = _encrypt_aes(message)
    return pickle.dumps({'secured_data': pickle.dumps(
        {
            "iv":aes_encrypted_data['iv'], 
            "cipher_txt":aes_encrypted_data['cipher_txt']
        }), 
        'secured_key':_encrypt_rsa(public_key, aes_encrypted_data['key'])})


def decrypt_msg(private_key, encrypted_msg):
    encrypted_msg = pickle.loads(encrypted_msg)
    secured_data = pickle.loads(encrypted_msg.pop('secured_data',[]))
    key = _decrypt_rsa(private_key, encrypted_msg.pop('secured_key',[]))
    return _decrypt_aes(key, 
        secured_data.pop('iv',[]), 
        secured_data.pop('cipher_txt',[]))


## api for ids
def random_id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def random_id_generator_with_custom_length(length):
    random_string = random.choice(string.ascii_lowercase + string.ascii_uppercase)
    for i in range(1,length):
        random_string = random_string + random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    return random_string


## generate public_key from private_key
## api for keys
def generate_public_key(private_key):
    return private_key.publickey()


## Rivest, Shamir, Adleman
## RSA for generating keys
def generate_private_key():
    rand = Random.new().read
    return RSA.generate(1024, rand)

## [END] public apis

## [BEGIN] apis not allowed to override 
## generate uuid based on host id and current time
def __uuid_generator_1():
    return uuid.uuid1()


## generate random uuid
def __uuid_generator_4():
    return uuid.uuid4()

"""
def __get_logger(logger_name):
    ## [BEGIN]logger settings 
    logger = getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("%(module)s : %(funcName)s : %(lineno)d : %(message)s")
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    ## [END]
    return logger"""

def __get_logger(logger_name): 
    FORMAT = "%(module)s : %(funcName)s : %(lineno)d : %(message)s"
    logging.basicConfig(format=FORMAT)
    logger = getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    return logger


def _get_current_time():
    return datetime.datetime.now()#tz=timezone('Europe/Helsinki'))


def _get_unix_from_datetime(dt):
    return calendar.timegm(dt.timetuple())

def _get_expiration_time():
    return datetime.datetime.now() + timedelta(minutes=SESSION_EXTENDED_BY)


#def _get_session_key():
#    return pickle.dumps(os.urandom(24))

def _generate_session_id():
    return str(uuid.UUID(bytes=OpenSSL.rand.bytes(16)))


def uuid_to_obj(s):
    if s is None:
        return None
    try:
        s = uuid.UUID(s)
    except ValueError:
        return None
    except AttributeError:
        return None
    else:
        return s

## [END] apis not allowed to override 


## references
# http://blog.cryptographyengineering.com/2012/05/how-to-choose-authenticated-encryption.html
# http://www.cryptofails.com/post/70059609995/crypto-noobs-1-initialization-vectors