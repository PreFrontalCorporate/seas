# models/client.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    plan_id = Column(Integer, ForeignKey('plans.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    trial_end_date = Column(DateTime)

    plan = relationship('Plan', back_populates='clients')
