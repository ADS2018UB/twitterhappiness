

import pymongo


def connect(credentials, collection_name):
    # connect to mLab DB
    try:
        with open(credentials, 'r', encoding='utf-8') as f:
            [name, password, url, dbname] = f.read().splitlines()
            db_conn = pymongo.MongoClient("mongodb://{}:{}@{}/{}".format(name, password, url, dbname))
            print ("DB connected successfully!!!")
    except pymongo.errors.ConnectionFailure as e:
        print ("Could not connect to DB: %s" % e)

    db = db_conn[dbname]
    collection = db[collection_name]

    return collection
