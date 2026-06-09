from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    city = Column(String)
    education = Column(String)
    # Added simple login credentials
    email = Column(String, unique=True, index=True)
    password = Column(String)
