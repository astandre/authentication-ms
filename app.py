from flask import Flask, request
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from flask_mail import Mail, Message
from sqlalchemy_utils import EncryptedType
from random import randrange
import os

app = Flask(__name__)
if config('DEBUG'):
    app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL_DEV')
    key = config('KEY')
else:
    key = os.environ.get('KEY')
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True

heroku = Heroku(app)
db = SQLAlchemy(app)
mail = Mail(app)

mail.init_app(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(EncryptedType(db.String, key), nullable=False)
    pin = db.Column(db.String(4), nullable=True)
    question = db.Column(db.String(50), nullable=True)
    answer = db.Column(EncryptedType(db.String, key), nullable=True)

    def __repr__(self):
        return f'{self.user_name}'


@app.route('/authenticate', methods=['POST'])
def authenticate():
    if request.method == 'POST':
        user = User.query.filter_by(user_name=request.json["user_name"]).first()
        if user is None:
            return {"success": False, "message": "User not found", "status": 404}
        else:
            if request.json["method"] == "pin":
                if "pin" in request.json:
                    if request.json["pin"] == user.pin:
                        return {"success": True, "status": 200}
                    else:
                        return {"success": False, "message": "Wrong PIN", "status": 200}
                else:
                    return {"success": False, "message": "Must provide a PIN", "status": 404}
            elif request.json["method"] == "password":
                if "password" in request.json:
                    if request.json["password"] == user.password:
                        return {"success": True, "status": 200}
                    else:
                        return {"success": False, "message": "Wrong password or username", "status": 200}
                else:
                    return {"success": False, "message": "Must provide username and password", "status": 404}
            elif request.json["method"] == "question":
                if "answer" in request.json:
                    if request.json["answer"].lower() == user.answer:
                        return {"success": True, "status": 200}
                    else:
                        return {"success": False, "message": "Wrong answer for question", "status": 200}
                else:
                    return {"success": False, "message": "Must provide an answer", "status": 404}
            else:
                return {"success": False, "message": "Must provide a valid authentication mechanism", "status": 400}
    else:
        return {"error": "Method now allowed", "status": 503}


@app.route('/request/pin', methods=['POST'])
def request_pin():
    if request.method == 'POST':
        user = User.query.filter_by(user_name=request.json["user_name"]).first()
        if user is None:
            return {"message": "User not found", "status": 404}
        else:
            user.pin = randrange(9999)
            db.session.commit()
            msg = Message("Security PIN",
                          sender=config('MAIL_USERNAME'),
                          recipients=[user.email])
            msg.body = f"Hello {user.user_name}, your security PIN is: {user.pin}"
            mail.send(msg)
            print(f"User: {user.user_name} has security Pin {user.pin}")
            return {"message": "Pin has been sent to email", "status": 200}
    else:
        return {"error": "Method now allowed", "status": 503}


@app.route('/user/new', methods=['POST'])
def new_user():
    if request.method == 'POST':
        data = request.get_json()
        user = User(user_name=data["user_name"], password=data["email"], email=data["password"])
        if "question" in data and "answer" in data:
            user.question = data["question"]
            user.answer = data["answer"]

        db.session.add(user)
        db.session.commit()
        return {"message": "User created", "user": user.id, "status": 200}
    else:
        return {"error": "Method now allowed", "status": 503}


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host=os.environ.get('HOST'), debug=os.environ.get('DEBUG'))
