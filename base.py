from dotenv import load_dotenv
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

engine = create_engine(os.environ["engine"])
Session = sessionmaker(bind=engine)

Base = declarative_base() 
