import logging

__author__ = 'Dominik'

FORMAT = "%(filename)s:%(funcName)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
log = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base
from db_config import database

engine = create_engine(database)
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
