from flask import Flask, request
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from flask_mail import Mail, Message
from sqlalchemy_utils import EncryptedType
from random import randrange
import os

app = Flask(__name__)
# if os.environ.get('DEBUG'):
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL_DEV')
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

key =  os.environ.get('KEY')


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(EncryptedType(db.String, key), nullable=False)
    pin = db.Column(db.String(4), nullable=True)

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
            else:
                return {"success": True}
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


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host= os.environ.get('HOST'), debug= os.environ.get('DEBUG'))
#
