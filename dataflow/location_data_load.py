
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


# define list of locations to be considered
locations = [
    {
        "name": "Barcelona",
        "box": [2.03,41.2845,2.3184,41.4958]
    },
    {
        "name": "Madrid",
        "box": [-3.887581,40.328514,-3.516543,40.518785]
    },
    {
        "name": "New York",
        "box": [-74.5236,40.4938,-73.4606,40.9642]
    },
]


DB_CREDENTIALS = "../credentials/mlab_credentials.txt"
DB_LOCATIONS_COLLECTION = "twitter_happiness_locations"
db_locations = connect(DB_CREDENTIALS, DB_LOCATIONS_COLLECTION)


# retrieve existing locations
print(db_locations.count_documents({}), " existing documents:")
for location in db_locations.find():
    print(" ", location)


# delete existing locations
result = db_locations.delete_many({})
print(result.deleted_count, " documents deleted")


# load defined locations
for location in locations:
    location["lat_min"] = location["box"][1]
    location["lat_max"] = location["box"][3]
    location["lon_min"] = location["box"][0]
    location["lon_max"] = location["box"][2]
    db_locations.replace_one({"name":location["name"]}, location, upsert = True)


# retrieve loaded locations
print(db_locations.count_documents({}), " documents loaded:")
for location in db_locations.find()[:10]:
    print(" ", location)