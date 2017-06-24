import logging

FORMAT = "%(filename)s:%(funcName)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
log = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tasker.model import Base
from tasker.db_config import database

__author__ = 'Dominik'


engine = create_engine(database)
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)

