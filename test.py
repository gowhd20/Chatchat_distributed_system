from flask import Flask, request, render_template

app = Flask(__name__)
 
@app.route("/")
def index():
    page = 'overview'
    data = {
        'page': page,
    }
    print 'are you here'
    return render_template('tt.html')
 
@app.route("/echo", methods=['POST'])
def echo(): 
    return "You said: " + request.form['text']
 
 
if __name__ == "__main__":
    app.run()