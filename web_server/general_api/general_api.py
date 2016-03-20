import random, string, uuid
import pickle
import hashlib
import base64

from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
import logging
from logging import getLogger

## Advanced Encryption Standard
## encrypt text with aes, generate iv and wrap altogether in json format with nonce from cipher
## nonce is going to be used when decrypt aes
## cipher generates nonce and encrypts message with iv 
def _encrypt_aes(raw_txt):
    key = hashlib.sha256(get_random_bytes(AES.block_size)).digest() # => a 32 byte string
    padded_txt = _padding(raw_txt)
    iv = Random.new().read(AES.block_size)   
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return {'key': key, 'iv': iv, 'cipher_txt': base64.b64encode(cipher.encrypt(padded_txt))}

# encrypt iv with public_key
def _encrypt_rsa(public_key, key):
    if type(public_key) is unicode:
        public_key = RSA.importKey(public_key)
    cipher_rsa = PKCS1_OAEP.new(public_key)
    return cipher_rsa.encrypt(key)

## encrypt message between clients and web server
def encrypt_msg(public_key, message):
    aes_encrypted_data = _encrypt_aes(message)
    return pickle.dumps({'secured_data': pickle.dumps(aes_encrypted_data), 
        'secured_key':_encrypt_rsa(public_key, aes_encrypted_data['key'])})

def _padding(txt):
    return txt+(AES.block_size-len(txt)%AES.block_size)*chr(AES.block_size-len(txt)%AES.block_size)

# decrypt text using key from aes algorithm
def _decrypt_aes(key, iv, cipher_txt):
    #print "key: "+key
    #print "iv:  "+iv
    #print "cipher:  "+cipher_txt
    cipher_txt = base64.b64decode(cipher_txt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    test =  cipher.decrypt(cipher_txt)
    return unpadding(test.decode('utf-8'))

## Rivest, Shamir, Adleman
## decrypt iv encrypted by sender's public key to decrypt message content was encrypted with aes
def _decrypt_rsa(private_key, secured_key):
    if type(private_key) is unicode:
        private_key = RSA.importKey(private_key)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    return cipher_rsa.decrypt(secured_key)
def unpadding(txt):
    return txt[:-ord(txt[len(txt)-1:])]

## decrypt    //
def decrypt_msg(private_key, encrypted_msg):
    #print encrypted_msg
    encrypted_msg = pickle.loads(encrypted_msg)
    #print encrypted_msg
    secured_data = pickle.loads(encrypted_msg.pop('secured_data',[]))
    key = _decrypt_rsa(private_key, encrypted_msg.pop('secured_key',[]))
    return _decrypt_aes(key, 
        secured_data.pop('iv',[]), 
        secured_data.pop('cipher_txt',[]))

## api for ids
def random_id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def random_id_generator_with_custom_Length(length):
    random_string = random.choice(string.ascii_lowercase + string.ascii_uppercase)
    for i in range(1,length):
        random_string = random_string + random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    return random_string

## generate uuid based on host id and current time
def uuid_generator_1():
	return uuid.uuid1()

## generate random uuid
def uuid_generator_4():
	return uuid.uuid4()

## generate public_key from private_key
## api for keys
def generate_public_key(private_key):
    return private_key.publickey()

## Rivest, Shamir, Adleman
## RSA for generating keys
def generate_private_key():
    rand = Random.new().read
    return RSA.generate(1024, rand)

def get_logger(logger_name):
    ## [BEGIN]logger settings 
    logger = getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    ## [END]
    return logger