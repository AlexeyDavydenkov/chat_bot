from datetime import datetime

import peewee as pw

db = pw.SqliteDatabase('lecture.db')

class ModelBase(pw.Model):
    created_at = pw.DateField(default=datetime.now())

    class Meta():
        database = db

class History(ModelBase):
    message = pw.TextField()
    number = pw.TextField()

    @classmethod
    def clean_history(cls):
        query = cls.select().order_by(cls.created_at.asc())
        count = query.count()

        if count > 10:
            old_records = query.limit(count - 10)
            for record in old_records:
                record.delete_instance()
