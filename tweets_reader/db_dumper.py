from pymongo import MongoClient

MLAB_CREDENTIALS_FILE = '../credentials/mlab_credentials.txt'


class Dumper:
    def __init__(self):
        # connect here
        with open(MLAB_CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            [name, password, url, dbname] = f.read().splitlines()

        mongo_url = "mongodb://{}:{}@{}/{}".format(name, password, url, dbname)
        self.client = MongoClient(mongo_url)

        print("DB connected successfully!!!")
        print("\t", name, url, dbname)

    def dump_tweet(self, tweet):
        # dump to the database
        pass


d = Dumper()
