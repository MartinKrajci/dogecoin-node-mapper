from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("postgresql://postgres:dogepass@db:5432/dogecoin_mapper")
session = scoped_session(sessionmaker(bind=engine))
base = declarative_base()