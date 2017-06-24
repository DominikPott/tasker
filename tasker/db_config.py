import os, inspect

db_type = r'sqlite:///'

db_path = os.getenv('TASKER_DB')
print db_path
if not db_path:
    import tasker
    tasker_dir = os.path.dirname(inspect.getfile(tasker))
    default_db = 'tasker.db'
    db_path= os.path.join(tasker_dir, default_db)

database = db_type + db_path
