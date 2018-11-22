
# main file for the daily dafaflow (ETL)
# try it by executing: python main_daily.py


import db_connection
from data_extraction import DataExtraction
import data_transformation
import data_load
import tweepy


DB_CREDENTIALS = "../credentials/mlab_credentials.txt"
TWITTER_CREDENTIALS = '../credentials/twitter_credentials.txt'
DB_LOCATIONS_COLLECTION = "twitter_happiness_locations"


if __name__ == '__main__':

    db_locations = db_connection.connect(DB_CREDENTIALS, DB_LOCATIONS_COLLECTION)

    with open(TWITTER_CREDENTIALS, 'r', encoding='utf-8') as f:
        [access_key, access_secret, consumer_key, consumer_secret] = f.read().splitlines()

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    twitter_api = tweepy.API(auth)
    print("twitter connection successful\n")

    de = DataExtraction(twitter_api)

    for location in db_locations.find():
        print("Processing data for ", location["name"])

        # extraction: download tweets from Twitter API
        data = de.collect(location)

        # transformation: process/analyze downloaded tweets
        data_processed = data_transformation.analyze(data)

        # load: load processed tweets into the DB

        data_load.load(DB_CREDENTIALS,data_processed)

        print("Completed\n")
