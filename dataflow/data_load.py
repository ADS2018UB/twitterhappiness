# functions to load processed tweets into the DB
# input: processed tweets
# output:
import pymongo


class DataLoad:
    def __init__(self, credentials):
        print('Connecting to the database')

        try:
            with open(credentials, 'r', encoding='utf-8') as f:
                [name, password, url, dbname] = f.read().splitlines()
                self.conn = pymongo.MongoClient("mongodb://{}:{}@{}/{}".format(name, password, url, dbname))
                print("Connected successfully!!!")
        except pymongo.errors.ConnectionFailure as e:
            print("Could not connect to MongoDB: %s" % e)
        pass

    def load(self, data):

        print('Inserting tweets collected into the database')
        # Create a database object - database is twitter_happiness
        db = self.conn.twitter_happiness
        # Create a collection object - collection is tweets
        collection = db.tweets
        # Check if the tweets collected are in the database and if not insert them
        inserted = 0
        discarded = 0
        for tweet in data:
            id_tweet = tweet['id']
            if bool(collection.find_one({"id": id_tweet})):
                discarded += 1
            else:
                inserted += 1
                collection.insert_one(tweet)

        print('Inserted tweets: ', inserted)
        print('Discarded tweets: ', discarded)
