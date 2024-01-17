from peewee import SqliteDatabase, Model, CharField, DateTimeField, TextField


db = SqliteDatabase('rss_reader.db')


class Entry(Model):
    channel_name = CharField()
    title = CharField()
    summary = TextField(null=True)
    link = CharField(unique=True)
    published = DateTimeField(null=True)
    created = DateTimeField(null=True)

    class Meta:
        database = db


db.connect()
db.create_tables([Entry])