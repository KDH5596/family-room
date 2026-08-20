from sqlalchemy import Column, Integer, String, Text
from database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String)
    email = Column(String)
    picture = Column(String)
    title = Column(String)
    content = Column(Text)
    room = Column(String)
    category = Column(String)