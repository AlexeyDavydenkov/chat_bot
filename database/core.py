from database.utility.CRUD import CRUDInteface
from database.common.models import db, History

db.connect()
db.create_tables([History])
# db.close()

crud = CRUDInteface()

if __name__ == '__main__':
    crud()