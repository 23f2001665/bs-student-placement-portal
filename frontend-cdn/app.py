from flask import Flask, render_template

app = Flask(__name__, template_folder='.', static_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

@app.get('/ping')
def ping():
    return {"message": "Pong from 8000!"}

if __name__ == '__main__':
    app.run(debug=True, port=8000)
    