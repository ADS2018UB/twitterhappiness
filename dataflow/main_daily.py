

import pymongo

import data_collection
import data_analysis
import data_load


DB_LOCATIONS = "twitter_happiness_locations"


def db_connection(collection_name):
    # connect to mLab DB
    try:
        with open("../credentials/mlab_credentials.txt", 'r', encoding='utf-8') as f:
            [name, password, url, dbname] = f.read().splitlines()
            db_conn = pymongo.MongoClient("mongodb://{}:{}@{}/{}".format(name, password, url, dbname))
            print ("DB connected successfully!!!")
    except pymongo.errors.ConnectionFailure as e:
        print ("Could not connect to DB: %s" % e)

    db = db_conn[dbname]
    collection = db[collection_name]

    return collection


if __name__ == '__main__':

    db_collection = db_connection(DB_LOCATIONS)

    print()
    for location in db_collection.find():
        print("Processing data for ", location["name"])
        data = data_collection.collect(location)
        data_processed = data_analysis.analize(data)
        data_load.load(data_processed)
        print("Completed")
        print()
