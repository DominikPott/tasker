"""tasker project management package.

the :mod:`tasker` module contains a model view control stucture to view and manipulate task data.

- :mod:`tasker.model`
- :mod:`tasker.control`
- :mod:`tasker.ui`
- :mod:`tasker.db_cofig`
- :mod:`tasker.templates`


One can use the :func:`tasker.control.new_project` to create a new project in the database to hold tasks relationships
and states.

Example:

>>> import tasker.control
>>> tasker.control.new_project(name='test_project')
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

