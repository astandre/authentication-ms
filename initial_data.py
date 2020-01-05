from app import User
from app import db

db.create_all()

db.session.add(
    User(user_name='andre', password='pass', email="andreherera97@gmail.com", question="Nombre de tu primer perro",
         answer="enki"))
db.session.add(User(user_name='Janfer1798', password='56789', email="zhoyi1798@gmail.com"))

db.session.commit()
print("Done")
