"""
This file is uses to specifie the database type and its location on the file system.
The first step to determin the database location is to look up the env variable TASKER_DB.
If this isn't existing the database will be located in the tasker module as tasker.db.
"""
import os, inspect

db_type = r'sqlite:///'
db_path = os.getenv('TASKER_DB')
if not db_path:
    import tasker
    tasker_dir = os.path.dirname(inspect.getfile(tasker))
    default_db = 'tasker.db'
    db_path = os.path.join(tasker_dir, default_db)

database = db_type + db_path
