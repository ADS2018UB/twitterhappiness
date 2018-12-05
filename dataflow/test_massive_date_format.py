import pymongo


def connect():
    
    try:
        name = 'ads2018'
        password = 'ads2018'
        url = 'ds211774.mlab.com:11774'
        dbname = 'twitter_happiness'
        conn = pymongo.MongoClient("mongodb://{}:{}@{}/{}".format(name, password, url, dbname))
        print("Connected successfully!!!")
        return conn
    except pymongo.errors.ConnectionFailure as e:
        print("Could not connect to MongoDB: %s" % e)
