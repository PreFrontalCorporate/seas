# models/usage.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class UsageLog(Base):
    __tablename__ = 'usage_logs'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    endpoint = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    usage_cost = Column(Integer)  # Cost in credits

    client = relationship('Client')
