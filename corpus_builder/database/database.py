import datetime
import enum

from mongoengine import *


class Source(enum.Enum):
    GOV_UK_NEWS = 1
    TELEGRAPH = 2
    GUARDIAN = 3
    SUN = 4
    WEFORUM = 5


class Post(Document):
    # Required
    source = StringField(required=True)
    url = StringField(required=True, unique=True)
    content = StringField(required=True)
    id_custom = IntField(required=True)

    # Everything from this line onwards is optional

    scrape_datetime = DateTimeField(default=datetime.datetime.now)

    # gov.uk
    author = StringField()
    title = StringField()
    date = StringField()
    description = StringField()
    format = StringField()
    taxon_slug = StringField()

    # Telegraph
    tags = ListField(StringField())

    # Weforum
    category = StringField()
    keywords = ListField(StringField())
