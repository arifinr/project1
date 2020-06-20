from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from flask_login import UserMixin
from database import Base

class User(UserMixin, Base):
    __tablename__ = 'users'
    username = Column(String(100), primary_key=True) # primary keys are required by SQLAlchemy
    email = Column(String(100), unique=True)
    name = Column(String(100))
    password = Column(String(100))

    def __init__(self, username=None, name=None, email=None, password=None):
        self.username = username
        self.name = name
        self.email = email
        self.password = password

    def get_id(self):
           return (self.username)

    def __repr__(self):
        return '<User %r>' % (self.name)