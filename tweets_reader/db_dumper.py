from pymongo import MongoClient
from tweets_reader import get_tweets

MLAB_CREDENTIALS_FILE = '../credentials/mlab_credentials.txt'


class Dumper:
    def __init__(self):
        # make connection
        with open(MLAB_CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            [name, password, url, dbname] = f.read().splitlines()

        mongo_url = "mongodb://{}:{}@{}/{}".format(name, password, url, dbname)
        self.client = MongoClient(mongo_url)

        print("DB connected successfully!!!")
        print("\t", name, url, dbname)

    def dump_tweet(self, tweet):
        # dump to the database
        db = self.client.twitter_happiness
        db.tweets.insert_one(tweet)
        pass


def test():
    d = Dumper()
    tweets = get_tweets([-75.3325, 40.0274, -71.6961, 41.4725], 5)
    d.dump_tweet(tweets[0])
