from flask import Flask
from extension import db
from model import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"

db.init_app(app)

@app.route("/create_all")
def create_all():
    db.create_all()
    return "Database tables created!"

@app.route("/show_programmes")
def show_programmes():
    programmes = Programme.query.all()
    print(programmes)
    return str(programmes)

@app.route("/show_branches")
def show_branches():
    branches = Branch.query.all()
    return "<br>".join(['1', '2', '3'])

if __name__ == "__main__":
    print(Programme, Branch)
    app.run(debug=True)