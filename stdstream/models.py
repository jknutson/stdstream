from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LogEntry(Base):
  __tablename__ = 'log_entries'

  id = Column(Integer, primary_key=True)
  data = Column(String(255))

  def __repr__(self):
    return '<LogEntry(id=%s)>' % self.id

class RsyncLog(Base):
  __tablename__ = 'rsync_logs'
  # log format = %t|%p|%i|%n|%l|%b
  id = Column(Integer, primary_key=True)
  timestamp = Column(DateTime)
  pid = Column(Integer)
  itemized_changes = Column(String(12))
  filename = Column(String(255))
  bytes_transferred = Column(Integer)

def drop_tables():
  global Base
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from config import config
  engine = create_engine(config['SQLALCHEMY_URI'])
  Base.metadata.drop_all(engine)

def create_tables():
  global Base
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from config import config
  engine = create_engine(config['SQLALCHEMY_URI'])
  Base.metadata.create_all(engine)

