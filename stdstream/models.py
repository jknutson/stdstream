from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LogEntry(Base):
  __tablename__ = 'log_entries'

  id = Column(Integer, primary_key=True)
  data = Column(String(255))

  def __repr__(self):
    return '<LogEntry(id=%s)>' % self.id

def create_tables():
  global Base
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from config import config
  print config
  engine = create_engine(config['SQLALCHEMY_URI'])
  Base.metadata.create_all(engine)
