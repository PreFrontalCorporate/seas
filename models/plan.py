# models/plan.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Plan(Base):
    __tablename__ = 'plans'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)  # Price in cents (USD)
    description = Column(String)
    is_active = Column(Boolean, default=True)
