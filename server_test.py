import callme

proxy = callme.Proxy(amqp_host='localhost', server_id='haejong', amqp_port=5672)

print(proxy.use_server(server_id='haejong').add(1, 1))
