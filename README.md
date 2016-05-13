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
	- Python with many other plugins e.g)flask, callme proxy, Crypto, WSGI ... 
	- Rabbitmq server
	- MongoDB
	
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
	User information is stored in 'Sessions' document that has a lifetime of pre-defined timedelta value.
	Session data is at first maintained by indivisual master nodes and once get pushed into shared resource database, it stays 
	as long as someone decide to clean the whole system.
	Each master node cleans its session data by pre-defined time of interval. If the data was cleaned, corresponding user loses his
	data history and only way to get them back is retrieving from shared resource database.
	User without history of previous session id will be assigned a new session id when logging in which has empty links to other documents.
	
	
## Fault tolerance and recovery
	A number of master nodes(also alias coordinator) can run concurrently and by doing so, if master node in charge went down, other backup
	master nodes can occupy the empty space. This will happen gracefully by slave nodes start looking for backup master node
	when previous master node stop responding. Once it finds backup master node, it starts from registering as if it was a new slave node.
	On the other side, if slave node stops responding, master node will try pre-defined times and decide to move on to another slave node.
	Using session allows for users to restore all the data from the database in either shared resource database or master node in case closing blowser.
	
		
## Security 
	The system leverages AES and RSA(symmetric and asymmetric key) to keep the travling data secure.
	Slave node sends its public key at the handshaking phase to the master node, and the master node handshakes back to the node with the data of
	common-RSA key(for fanout message encryption/decryption) as well as general server info(ex, server's public_key, id).
	Also master server refreshes common-RSA keys for every pre-defined time of interval and send them out to all slave nodes to update which would increase level of security.
	
	
## Communication
	List of communication methods are as follows: publish/subscribe, RPC, fanout, direct messaging(downstream/upstream).
	Master and slave nodes all have the same capacity of communication methods.
	When a new node joins, present master node fanout broadcast messages to all slave nodes with its info using publish/subscribe communication method.
	Slave nodes send/receive direct message to the master node as needed(ex, acquiring permission to shared resource). And also Master node responses 
	with direct messaging.
	All slave nodes keep up-to-date their status to the present master node by RPC.
	Once again if any slave node has been disconnected, the present master node broadcast messages to all slave nodes and updates active node information in both
	master and slave side of database.
	
	
## Naming
	Everything is dynamically handled from communication between nodes to database hits 
	
	
## Consistency and replication
	All user history is replicated onto shared resource center thus, as long as the session id is valid, users can fully restore data from either of both database.
	Any crashes from either slave node or master node is handled gracefully and automatically. Also data consistency is achived by enabling replicas to the shared resource database.
	Each master node make own logs about major actions and store them into the database so that we expect it for clarifying what has happened while it's running. 
	
## Coding structure
	object-oriented style