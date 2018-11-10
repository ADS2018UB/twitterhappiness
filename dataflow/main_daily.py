
# main file for the daily dafaflow (ETL)
# try it by executing: python main_daily.py


import db_connection
import data_collection
import data_analysis
import data_load


DB_CREDENTIALS = "../credentials/mlab_credentials.txt"
DB_LOCATIONS_COLLECTION = "twitter_happiness_locations"


if __name__ == '__main__':

    db_locations = db_connection.connect(DB_CREDENTIALS, DB_LOCATIONS_COLLECTION)

    print()
    for location in db_locations.find():
        print("Processing data for ", location["name"])

        # extraction: download tweets from Twitter API
        data = data_collection.collect(location)

        # transformation: process/analize downloaded tweets
        data_processed = data_analysis.analize(data)

        # load: load processed tweets into the DB
        data_load.load(data_processed)

        print("Completed")
        print()
