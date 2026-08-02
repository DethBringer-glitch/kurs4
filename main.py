from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine('sqlite:///bsa.db')
base = declarative_base()

class immenineg(base):
    __tablename__ = 'immenineg'
    immenineg = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(String)
    gifts = Column(String)
    cakes = Column(String)

base.metadata.create_all(engine)
Session = sessionmaker(engine)
s = Session()
s.merge(immenineg(immenineg(name='Миша', data='31/10/2014', gifts='Meta Quest 3', cakes='Наполеон', immenineg=1)))
s.commit()

