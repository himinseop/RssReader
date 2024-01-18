from peewee import SqliteDatabase, Model, CharField, DateTimeField, TextField


db = SqliteDatabase('rss_reader.db')


class Entry(Model):
    channel_name = CharField()
    link = CharField(unique=True)
    title = CharField()
    summary = TextField(null=True)
    author = TextField(null=True)
    image_url = TextField(null=True)
    published = DateTimeField(null=True)
    created = DateTimeField(null=True)

    class Meta:
        database = db


db.connect()
db.create_tables([Entry])
