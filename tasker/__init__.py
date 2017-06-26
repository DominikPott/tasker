"""tasker project management package.

the :mod:`tasker` module contains a model view control stucture to view and manipulate task data.

- :mod:`tasker.model`  # Database strucktures
- :mod:`tasker.control`  # Main api to work with
- :mod:`tasker.ui`  # To display data to the end user and let them manipulate it.
- :mod:`tasker.db_config`  # Location and type of the database you want to use.
- :mod:`tasker.templates`  # templates for task and task dependencies.


The main api module is :mod:`tasker.control`. This holds common functions to generate and manipulate tasks.

"""

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

