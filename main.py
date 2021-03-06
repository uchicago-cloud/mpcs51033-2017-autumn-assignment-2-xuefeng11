import cgi
import datetime
import urllib
import webapp2
import json
import logging
import os
import base64
from uuid import uuid4
import time
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import images
import cloudstorage
from google.appengine.api import app_identity
from google.appengine.api import urlfetch


from models import *

# delete image in google cloud storage
def CloudDeleteImage(filename):

    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    bucket = '/' + bucket_name
    filename = bucket + '/' + filename

    try:
        cloudstorage.delete(filename)
    except cloudstorage.NotFoundError:
        pass

#Store image in google cloud storage
def CloudStoreImage(file, filename):
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    bucket = '/' + bucket_name
    filename = bucket + '/'+ filename
    cloudstorage_file = cloudstorage.open(filename, 'w', content_type='image/png')
    cloudstorage_file.write(file)
    cloudstorage_file.close()

#Read image from google cloud storage
def CloudReadImage(filename):
    bucket_name = os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name())
    bucket = '/' + bucket_name
    filename = bucket + '/' + filename
    cloudstoragefile = cloudstorage.open(filename)
    return cloudstoragefile.read()

#get label by detecting image through google vision api
def VisionLabelDetection(bucketname,filename,thumbnail):
    labels=[]
    #if run local server, sent image, if on google cloud sent share link to api
    if bucketname == 'app_default_bucket':
        data = '{"requests": [{"features": [{"type": "LABEL_DETECTION","maxResults": "3"}], "image": {"content": "%s"}}]}' % (
        base64.b64encode(thumbnail))
    else:
        data = '{"requests": [{"features": [{"type": "LABEL_DETECTION","maxResults": "3"}], "image": {"source": { "gcsImageUri": "gs://%s/%s"}}}]}' % (
        bucketname, filename)

    result = urlfetch.fetch(
        url='https://vision.googleapis.com/v1/images:annotate?key=AIzaSyD_GB8f4NeuKXPRaI5DF5HvjCWv9xlfAVA',
        headers={'Content-Type': 'application/json'},
        method=urlfetch.POST,
        payload=data
    )

    #extract all the labels
    str=json.loads(result.content)
    str2=str.get('responses')
    str3=str2[0].get('labelAnnotations')

    if str3 == None:
        return labels

    for temp in str3:
        labels.append(temp.get('description'))

    return labels

#######################################################################
# add user into ndb
class RegisterPostHandler(webapp2.RequestHandler):
    def post(self):

        if self.request.get('username'):
            username_ = self.request.get('username')

        user_result = User.exists(username_)

        if user_result:
            self.response.out.write("username already existed")
            return

        else:
            name_ = self.request.get('name')
            email_ = self.request.get('email')
            password_ = self.request.get('password')
            id_token_ = str(uuid4())
            user_ = User(parent=ndb.Key("User",username_),
                         name=name_,
                         email=email_,
                         unique_id=str(uuid4()),
                         username=username_,
                         password=password_,
                         id_token=id_token_
            )
            user_.put()
            logging.info("new user added")
            self.redirect('/?username=%s&id_token=%s'%(username_,id_token_))

#register new user
class RegisterHandler(webapp2.RequestHandler):
        def get(self):
            self.response.out.write('<html><body>')
            self.response.out.write("""
            <form action="/postRegister/" enctype="multipart/form-data" method="post">
            <div>name <input value="xuefeng" name="name"></div>
            <div>email <input value="xuefeng@uchicago.edu" name="email"></div>
            <div>username <input value="xuefeng111" name="username"></div>
            <div>password <input value="123456" name="password"></div>
            <div><input type="submit" value="Post"></div>
            </form>
            <hr>
            </body>
            </html>""")


################################################################################
"""The home page of the app"""

#home page to add image to user
class HomeHandler(webapp2.RequestHandler):

    """Show the webform when the user is on the home page"""
    def get(self):

        id_token = self.request.get('id_token')
        username = self.request.get('username')
        if id_token == '':
            self.response.content_type='application/json'
            self.response.status_int=401
            self.response.status_message=json.dumps("unauthorized access")
            self.response.out.write("HTTP 401 : Unauthorized access")
            return
        time.sleep(1)
        result=User.id_tokenUserValidate(username,id_token)
        if result == None:
            self.response.out.write("username and id_token validation failed,please run again")
            return

        self.response.out.write('<html><body>')

        # Print out some stats on caching
        stats = memcache.get_stats()
        self.response.write('<b>Cache Hits:{}</b><br>'.format(stats['hits']))
        self.response.write('<b>Cache Misses:{}</b><br><br>'.format(
                            stats['misses']))

        user = self.request.get('user')
        ancestor_key = ndb.Key("User", user or "*notitle*")
        # Query the datastore
        # photos = Photo.query_user(ancestor_key).fetch(100)

        self.response.out.write("""
        <form action="/post/%s/?id_token=%s" enctype="multipart/form-data" method="post">
        <div><textarea name="caption" rows="3" cols="60"></textarea></div>
        <div><label>Photo:</label></div>
        <div><input type="file" name="image"/></div>
        <div>User: <input type="text" name="username" value="%s" disabled><div>
        <div>id_token:  %s </div>
        <div><input type="submit" value="Post"></div>
        </form>
        <hr>
        </body>
        </html>""" % (username,id_token,username,id_token))


################################################################################
#return json format or web format of user datas after pass validation
class UserHandler(webapp2.RequestHandler):

    """Print json or html version of the users photos"""
    def get(self,username,type):

        id_token = self.request.get('id_token')
        if id_token == '':
            self.response.content_type='application/json'
            self.response.status_int=401
            self.response.status_message=json.dumps("unauthorized access")
            self.response.out.write("HTTP 401 : Unauthorized access")
            return

        result=User.id_tokenUserValidate(username,id_token)
        if result == None:
            self.response.out.write("username and id_token validation failed")
            return

        photos = self.get_data(username)
        photos_retrieved = []


        for key in photos:
            photos_retrieved.append(ndb.Key(urlsafe=key).get())


        if type == "json":
            output = self.json_results(photos_retrieved,username,id_token)
        else:
            output = self.web_results(photos_retrieved,username,id_token)
        self.response.out.write(output)

    def json_results(self,photos,username,id_token):
        """Return formatted json from the datastore query"""
        json_array = []
        for photo in photos:
            dict = {}
            dict['image_url'] = "image/%s/?id_token=%s" % (photo.key.urlsafe(),id_token)
            dict['caption'] = photo.caption
            dict['user'] = username
            dict['date'] = str(photo.date)
            dict['labels']=photo.labels
            json_array.append(dict)
        return json.dumps({'results' : json_array})

    def web_results(self,photos,username,id_token):
        """Return html formatted json from the datastore query"""
        html = ""
        for photo in photos:
            html += '<div><hr><div><img src="/image/%s/?id_token=%s" width="200" border="1"/></div>' % (photo.key.urlsafe(),id_token)
            html += '<div><blockquote>Caption: %s<br>User: %s<br>Date:%s</blockquote></div>' % (cgi.escape(photo.caption),username,str(photo.date))
            for label in photo.labels:
                html += '<div><blockquote>label: %s </div>' % (label)
            html += '</div>'
        return html

    @staticmethod
    def get_data(username):
        """Get data from the datastore only if we don't have it cached"""
        key = username + "_photos"
        data = memcache.get(key)
        if data is not None:
            logging.info("Found in cache")
            return data
        else:
            logging.info("Cache miss")
            ancestor_key = ndb.Key("User", username)
            data = User.query_user(ancestor_key)
            photo_=data.photos
            if not memcache.add(key, photo_, 3600):
                logging.info("Memcache failed")
        return photo_

################################################################################
"""Handle requests for an image ebased on its key"""
class ImageHandler(webapp2.RequestHandler):

    def get(self,key):
        id_token = self.request.get('id_token')
        if id_token == '':
            self.response.content_type='application/json'
            self.response.status_int=401
            self.response.status_message=json.dumps("unauthorized access")
            self.response.out.write("HTTP 401 : Unauthorized access")
            return

        result = User.getUserbyid_token(id_token)
        if result == None:
            self.response.out.write("id_token validation failed")
            return

        """Write a response of an image (or 'no image') based on a key"""
        photo = ndb.Key(urlsafe=key).get()
        file_=CloudReadImage(photo.image)
        if photo.image:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(file_)
        else:
            self.response.out.write('No image')

#delete image base on the key, delete ndb string and data on cloud storage
class ImageDeleteHandler(webapp2.RequestHandler):

        def get(self, key):
                id_token = self.request.get('id_token')
                if id_token == '':
                    self.response.content_type = 'application/json'
                    self.response.status_int = 401
                    self.response.status_message = json.dumps("unauthorized access")
                    self.response.out.write("HTTP 401 : Unauthorized access")
                    return

                result = User.getUserbyid_token(id_token)
                if result == None:
                    self.response.out.write("id_token validation failed")
                    return

                photo_keys = result.photos

                if key in photo_keys:
                    photo = ndb.Key(urlsafe=key).get()
                    CloudDeleteImage(photo.image)
                    key_photo = ndb.Key(urlsafe=key)
                    key_photo.delete()
                    photo_keys.remove(key)
                    result.photos=photo_keys
                    result.put()
                    logging.info("photo deleted")
                    self.response.out.write("photo deleted")
                else:
                    self.response.out.write("this photo is not in user's photos")

                key = result.username+"_photos"
                memcache.delete(key)


################################################################################
#write photo id to the ndb and photo data to the cloud storage
class PostHandler(webapp2.RequestHandler):
    def post(self,username):

        id_token = self.request.get('id_token')
        if id_token == '':
            self.response.content_type='application/json'
            self.response.status_int=401
            self.response.status_message=json.dumps("unauthorized access")
            self.response.out.write("HTTP 401 : Unauthorized access")
            return

        result=User.id_tokenUserValidate(username,id_token)
        if result == None:
            self.response.out.write("username and id_token validation failed")
            return
        # If we are submitting from the web form, we will be passing
        # the user from the textbox.  If the post is coming from the
        # API then the username will be embedded in the URL
        if self.request.get('username'):
            username = self.request.get('username')

        # Be nice to our quotas
        if images == None:
            self.response.out.write("no image uploaded")

        user_result = User.exists(username)

        if user_result:
            id_token_photo = str(uuid4())
            try:
                thumbnail = images.resize(self.request.get('image'), 100, 100)
                CloudStoreImage(thumbnail, id_token_photo)
            except:
                self.response.out.write("image is not valid")
                return
            #create photo by labels caption and photo_id
            photo_ = Photo(caption=self.request.get('caption'),
                           labels=VisionLabelDetection(os.environ.get('BUCKET_NAME',
                                 app_identity.get_default_gcs_bucket_name()),id_token_photo,thumbnail),
                           image=id_token_photo)
            photo_.put()
            user_result.photos.append(photo_.key.urlsafe())
            user_result.put()
            logging.info("new photo added to %s" % username)
            time.sleep(1)
            self.redirect('/user/%s/json/?id_token=%s' % (username,result.id_token))
        else:
            self.response.out.write("no user exist")

        #clear the cache
        key = username + "_photos"
        memcache.delete(key)

#logging
class LoggingHandler(webapp2.RequestHandler):
    """Demonstrate the different levels of logging"""

    def get(self):

        id_token = self.request.get('id_token')
        if id_token == '':
            self.response.content_type='application/json'
            self.response.status_int=401
            self.response.status_message=json.dumps("unauthorized access")
            self.response.out.write("HTTP 401 : Unauthorized access")
            return

        result=User.getUserbyid_token(id_token)
        if result == None:
            self.response.out.write("id_token validation failed")
            return

        logging.debug('This is a debug message')
        logging.info('This is an info message')
        logging.warning('This is a warning message')
        logging.error('This is an error message')
        logging.critical('This is a critical message')

        try:
            raise ValueError('This is a sample value error.')
        except ValueError:
            logging.exception('A example exception log.')

        self.response.out.write('Logging example.')

#authenticate the user to retrieve the token_id before process other steps
class AuthenticationHandler(webapp2.RequestHandler):
    def get(self):
        username_ = self.request.get('username')
        password_ = self.request.get('password')
        result = User.authenticate(username_,password_)

        if result:
            self.response.out.write(result.id_token)
            self.redirect('/?username=%s&id_token=%s' % (username_,result.id_token))
        else:
            self.response.out.write("username and password is not correct")


################################################################################

app = webapp2.WSGIApplication([

    # ?id_token= & username=
    ('/', HomeHandler),
    #?id_token=
    webapp2.Route('/logging/', handler=LoggingHandler),
    #?id_token=
    webapp2.Route('/image/<key>/', handler=ImageHandler),
    # ?id_token=
    webapp2.Route('/image/<key>/delete/', handler=ImageDeleteHandler),
    #?id_token=
    webapp2.Route('/post/<username>/', handler=PostHandler),
    #?id_token=
    webapp2.Route('/user/<username>/<type>/',handler=UserHandler),
    webapp2.Route('/register/', handler=RegisterHandler),
    webapp2.Route('/postRegister/', handler=RegisterPostHandler),
    #?username= & password=
    webapp2.Route('/user/authenticate/',handler=AuthenticationHandler)
    ],
    debug=True)
