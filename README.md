## Motivation & Introduction
A simple chatting system that fulfils components of distributed system
(sychronization, security, replication, consistency, fault tolerance, fail-over).

This system is built on web


## Realzed features
	- Fault tolerance and recovery
	- Consistency and replication
	- Naming
	- Security
	- Distributed synchronization
	- Modern style communication between nodes
	
## Tools
	- Python 
	- Rabbitmq server
	- MongoDB
	- Redis
	
## Featured security
Encryption
```python
def _encrypt_aes(raw_txt):
	key = hashlib.sha256(get_random_bytes(AES.block_size)).digest() # => a 32 byte string
	padded_txt = _padding(raw_txt)
	iv = Random.new().read(AES.block_size)   ## iv == nonce
	cipher = AES.new(key, AES.MODE_CBC, iv)
	return {'key': key, 'iv': iv, 'cipher_txt': base64.b64encode(cipher.encrypt(padded_txt))}  

	
def _padding(txt):
	return txt+(AES.block_size-len(txt)%AES.block_size)*chr(AES.block_size-len(txt)%AES.block_size)

	
def _encrypt_rsa(public_key, key):
	if type(public_key) is unicode:
		public_key = RSA.importKey(public_key)
	cipher_rsa = PKCS1_OAEP.new(public_key)
	return cipher_rsa.encrypt(key)


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
```	
Decryption
```python
def _decrypt_aes(key, iv, cipher_txt):
	cipher_txt = base64.b64decode(cipher_txt)
	cipher = AES.new(key, AES.MODE_CBC, iv)         
	test =  cipher.decrypt(cipher_txt)
	return _unpadding(test.decode('utf-8'))


def _decrypt_rsa(private_key, secured_key):
	if type(private_key) is unicode:
		private_key = RSA.importKey(private_key)
	cipher_rsa = PKCS1_OAEP.new(private_key)
	return cipher_rsa.decrypt(secured_key)

	
def _unpadding(txt):
	return txt[:-ord(txt[len(txt)-1:])]	
	

def decrypt_msg(private_key, encrypted_msg):
	encrypted_msg = pickle.loads(encrypted_msg)
	secured_data = pickle.loads(encrypted_msg.pop('secured_data',[]))
	key = _decrypt_rsa(private_key, encrypted_msg.pop('secured_key',[]))
	return _decrypt_aes(key, 
		secured_data.pop('iv',[]), 
		secured_data.pop('cipher_txt',[]))
	
```
## Session handling
	User information is stored in 'Sessions' document that 
	has a lifetime of pre-defined timedelta value.
	
	Session data is at first maintained by indivisual master nodes 
	and once it get pushed into shared resource database, 
	stays there and shared to other systems.
	
	Each master node cleans local session after 
	pushing it into shared database. 
	Shared data is accessed by the master node based on FIFO rule. 
	User without history of previous session id will be assigned 
	a new session id when logging in.
	
	
## System logging
	Each master node logs major commitment that it takes 
	into the local database
	
	
## Fault tolerance and recovery
	A number of master nodes(also alias coordinators) 
	can be running run concurrently. 
	By doing so, the system is able to handle 
	case of one of the master nodes' failure.
	Once the failure happens, involved worker nodes will automatically 
	migrate to another master node which is active.
	In a similar sense when new worker node joins to the system, 
	it iteratively searches for only active master node.
	When worker nodes detect master node stopped responding, 
	it start registering to another master node, 
	and then behave the same as if it was a new worker node.
	
	Also the end-users who interacting with 
	front-end(master node/coordinator) are redirected to
	another webpage while keeping all data in the shared database 
	when current webpage turns unavailable.
	
	On the other side, if worker node stops responding,
	master node will try over pre-defined times and then
	eventually asign the task to another worker node 
	in case of the worker node found failure.
	failed nodes are collected by each master node 
	and garbaged in every pre-defined time.
	All worker nodes in the list of failed worker nodes 
	will be omitted from every worker selection process.
	Using session allows for users to restore all the data 
	from either shared resource database or worker node database.
	
		
## Security 
	The system leverages AES and RSA(symmetric and asymmetric key) 
	together with nonce(initialization vector) to keep the travling data secure.
	
	Worker node sends its public key to the master node 
	at the stage of handshake, and then the master node handshakes back to the node 
	with data of common-RSA key(for fanout message encryption/decryption) 
	and general information of the master node(ex, server's public_key, id)
	encrypted by public key that the worker node just sent.
	
	Also master server refreshes common-RSA keys by every pre-defined time of interval and
	broadcast it to all worker nodes for updating.
	
	
## Communication
	List of communication methods this system is leveraging are as follows: 
	publish/subscribe, RPC, fanout, direct messaging(downstream/upstream).
	
	Master and worker nodes all have the same capacity of 
	communication within the nodes.
	
	When a new node joins or registered node leaves/fails master node 
	notifies to all worker nodes with its information 
	by the method of publish/subscribe(fanout, asynchronous).
	Worker nodes send/receive direct message to/from master node as needed(direct messaging, asynchronous). 
	
	Assignment of workload from master to worker node take place through RPC method(direct communication, synchronous).

	
## Distributed synchronization
	The system has chosen centralized sychronization algorithm for 
	accessing shared resource that is coordinator's permission based.

	When there is a request from the end-user, master node caches the task into the queue 
	to asign later when the turn comes.
	Otherwise master node(coordinator) asigns the task instantaneously to a worker node to process,
	and the access permission become locked.

	
## Naming
	Worker nodes are introduced about information including 
	other nodes' ids and RSA keys when it joins to a master node.
	
	
## Consistency and replication
	All data from user will be replicated/updated onto shared resource database with session id in which then 
	users can fully restore data from in case of node failure or webpage crash.
	
	Any crashes from either worker or master node are handled gracefully by automated redirection for the end-users. 
	
	Essential data is replicated locally in the worker node's database thus any requests can be handled gracefully
	even without permission to access shared resources(weakly-consistent).
	
	
## Coding structure
	object-oriented style
	
## Video demo
- redirecting end-user when current system is unavailable:
https://www.youtube.com/watch?v=L1taCQUoePE
	
- fail-over as master system falls into failure:
https://www.youtube.com/watch?v=75E4QDbO-Oo
	
- system(master-slave) (un)registration:
https://www.youtube.com/watch?v=PtDY8toMUPI
	