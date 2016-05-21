## Chatchat_distributed_system
A simple chatting system that fulfils components of distributed system features.
This project is centered on implementing key elements of the distributed systems

## Realzed features
	- Fault tolerance and recovery
	- Consistency and replication
	- Naming
	- Security
	- Distributed synchronization
	- Modern style communication between nodes
	
## Tools
	- Python with many other plugins e.g)flask, callme, Crypto, WSGI ... 
	- Rabbitmq server
	- MongoDB
	- Redis
	
## Featured security
	Encryption
	
	def _encrypt_aes(raw_txt):
		## hash keeps integrity of data, not to be changed
		## hash alias : message digest, checksum
		## encoding raw content is required if later it has to be compared with newly created hash by same input
		key = hashlib.sha256(get_random_bytes(AES.block_size)).digest() # => a 32 byte string
		padded_txt = _padding(raw_txt)
		iv = Random.new().read(AES.block_size)   ## iv == nonce
		cipher = AES.new(key, AES.MODE_CBC, iv)
		return {'key': key, 'iv': iv, 'cipher_txt': base64.b64encode(cipher.encrypt(padded_txt))}  

	
	## Is needed as the size of message differs each time
	def _padding(txt):
		return txt+(AES.block_size-len(txt)%AES.block_size)*chr(AES.block_size-len(txt)%AES.block_size)
	

	## asymetric key cryptography
	# encrypt key(symmetric key/AES) with receiver's public_key
	def _encrypt_rsa(public_key, key):
		if type(public_key) is unicode:
			public_key = RSA.importKey(public_key)
		cipher_rsa = PKCS1_OAEP.new(public_key)
		return cipher_rsa.encrypt(key)

		
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
		
	Decryption
	
	# decrypt text using key from aes algorithm
	def _decrypt_aes(key, iv, cipher_txt):
		cipher_txt = base64.b64decode(cipher_txt)
		cipher = AES.new(key, AES.MODE_CBC, iv)         
		test =  cipher.decrypt(cipher_txt)
		return _unpadding(test.decode('utf-8'))


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


	def decrypt_msg(private_key, encrypted_msg):
		encrypted_msg = pickle.loads(encrypted_msg)
		secured_data = pickle.loads(encrypted_msg.pop('secured_data',[]))
		key = _decrypt_rsa(private_key, encrypted_msg.pop('secured_key',[]))
		return _decrypt_aes(key, 
			secured_data.pop('iv',[]), 
			secured_data.pop('cipher_txt',[]))
		
	
## Session handling
	User information is stored in 'Sessions' document that 
	has a lifetime of pre-defined timedelta value.
	
	Session data is at first maintained by indivisual master nodes 
	and once it get pushed into shared resource database, 
	it stays as long as someone decide to clean the whole system.
	
	Each master node cleans its session data after 
	it succeed to push the data into shared database. 
	Data pushed into shared resource then shared to 
	all other nodes based on master node's permission. 
	User without history of previous session id will be assigned 
	a new session id when logging in.
	
	
## System logging
	Each master node logs major commitment that it takes 
	into the local database
	
	
## Fault tolerance and recovery
	A number of master nodes(also alias coordinators) 
	can run concurrently. 
	By doing so, system is able to handle 
	in case of one of the master nodes' failure.
	Once it happened, involved worker nodes will automatically 
	migrate to another master node that is active.
	In a similar sense when new worker node joins to the system, 
	it iteratively searches for only active master node.
	When worker nodes recognize master node stop responding, 
	it start registering to another master node, 
	and behave same as if it was a new worker node.
	
	Also the end-users who interacting with 
	front-end(master node/coordinator) are redirected to
	another webpage while keeping all data in the shared database 
	when current webpage turn unavailable.
	
	On the other side, if worker node stops responding,
	master node will try over pre-defined times and then
	eventually asign the task to another worker node 
	in case of the worker node found failure.
	failed nodes are collected by each master node 
	and garbaged in every pre-defined time.
	All worker node in the list of failed node 
	will be omitted in every worker selection process.
	Using session allows for users to restore all the data 
	from either of shared resource database or worker node database.
	
		
## Security 
	The system leverages AES and RSA(symmetric and asymmetric key) 
	to keep the travling data secure.
	
	Worker node sends its public key to the master node 
	at the stage of handshake, 
	and the master node handshakes back to the node 
	with data of common-RSA key(for fanout message encryption/decryption) 
	and general server info(ex, server's public_key, id)
	encrypted by public key of the worker node.
	
	Also master server refreshes common-RSA keys 
	for every pre-defined time of interval and
	broadcast new keys to all worker nodes for updating.
	
	
## Communication
	List of communication methods this system is leveraging are as follows: 
	publish/subscribe, RPC, fanout, direct messaging(downstream/upstream).
	
	Master and worker nodes all have the same capacity of 
	communication within the nodes.
	
	When a new node joins or registered node leaves/fails master node 
	notifies to all worker nodes 
	with its info by publish/subscribe(fanout, asynchronous) 
	communication method.
	Worker nodes send/receive direct message to/from 
	the master node as needed(direct messaging, asynchronous). 
	
	Assignment of workload from master node to worker node 
	takes place through RPC method(direct communication, synchronous).

	
## Distributed synchronization
	System selected centralized sychronization algorithm for 
	accessing shared resource that is coordinator's permission based.

	When there is a request from the end-user, master node caches 
	it in the queue and later asign the task
	to a worker node as soon as it takes turn from the queue 
	otherwise master node(coordinator) asigns
	the task instantaneously with permission to 
	the shared resource to a node to process. 
	
## Naming
	Worker nodes are introduced about information including 
	other node's ids and RSA keys when it joins to a master node.
	
	
## Consistency and replication
	All data from user will be replicated/updated onto 
	shared resource database with session id in which then 
	users can fully restore data from 
	in case of node failure or webpage crash.
	
	Any crashes from either worker or master node is 
	handled gracefully by automated redirect and searching for
	available nodes which will benefit 
	both entities of end-user and worker node.
	
	Essential data is replicated locally in the node database 
	therefore any requests can be handled gracefully
	even without permission to access shared resources(weakly-consistent).
	
	
## Coding structure
	object-oriented style
	
## Video demo
	- redirecting end-user when current system is available
	https://www.youtube.com/watch?v=L1taCQUoePE
	
	- fail-over as master system falls into failure
	https://www.youtube.com/watch?v=75E4QDbO-Oo
	
	- system(master-slave) (un)registration
	https://www.youtube.com/watch?v=PtDY8toMUPI
	