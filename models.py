from google.appengine.ext import ndb

class Photo(ndb.Model):
    """Models a user uploaded photo entry"""

    #image is used to store the photo id , which link to google cloud storage
    image = ndb.StringProperty()
    caption = ndb.StringProperty()
    #labels to store label detection from google vision api
    labels = ndb.StringProperty(repeated=True)
    date = ndb.DateTimeProperty(auto_now_add=True)

    #@classmethod
    #def query_user(cls, ancestor_key):
    #    """Return all photos for a given user"""
    #    return cls.query(ancestor=ancestor_key).order(-cls.date)

    #@classmethod
    #def query_user_alternate(cls, ancestor_key):
    #    """Return all photos for a given user using the gql syntax.
    #    It returns the same as the above method.
    #    """
    #    return ndb.gql('SELECT * '
    #                    'FROM Photo '
     #                   'WHERE ANCESTOR IS :1 '
     #                   'ORDER BY date DESC LIMIT 10',
     #                   ancestor_key)


class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    unique_id = ndb.StringProperty()
    #collection linked to each photo id
    photos = ndb.StringProperty(repeated=True)
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    id_token = ndb.StringProperty()

    @classmethod
    def query_user(cls,ancestor_key):
        result = ndb.gql('SELECT * FROM User WHERE ANCESTOR IS :1',ancestor_key).fetch()
        if result:
            return result[0]
        else:
            return None

    @classmethod
    def authenticate(cls,username,password):
        result=ndb.gql('SELECT * FROM User WHERE username = :1 and password = :2',username,password).fetch()
        if result:
            return result[0]
        else:
            return None

    @classmethod
    def exists(cls,username):
        result = ndb.gql('select * from User WHERE username = :1',username).fetch()
        if result:
            return result[0]
        else:
            return None

    @classmethod
    def id_tokenUserValidate(cls,username,id_token):
        result=ndb.gql('SELECT * FROM User WHERE username = :1 and id_token = :2',username,id_token).fetch()
        if result:
            return result[0]
        else:
            return None

    @classmethod
    def getUserbyid_token(cls,id_token):
        result=ndb.gql('SELECT * FROM User WHERE id_token = :1',id_token).fetch()
        if result:
            return result[0]
        else:
            return None