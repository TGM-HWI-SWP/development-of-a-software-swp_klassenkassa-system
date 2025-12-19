import os

if os.getenv("DB_MODE") == "memory":
    from . import db_memory as db
else:
    from . import db_mongo as db
