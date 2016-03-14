import callme
import threading


def add_text(username, text):
    global token, queueing_texts, is_token_holder
    if token is None:
        queueing_texts.append({'username': username, 'text_content': text, 'time': time.time()})
        return 'ADDED_TO_QUEUE'
    else:    
        # database connection
        conn = sqlite3.connect('data.sqlite')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        #run insert command
        insert_query = 'insert into chat (username, text_content, time) values (?, ?, ?)'
        cur.execute(insert_query, (username, text, time.time()))
            
        # commit and close database
        conn.commit()
        conn.close()
        return 'ADDED_TO_SERVER'
        

class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        
    def run(self):
        server = callme.Server(server_id='haejong', amqp_host='localhost', amqp_port=5672)
        server.start()

mWebserver = WebServer()
mWebserver.start()