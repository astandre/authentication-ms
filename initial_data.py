from app import User
from app import db

db.create_all()


db.session.add(User(user_name='andre', password='pass', email="andreherera97@gmail.com"))

db.session.commit()
print("Done")
