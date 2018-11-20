
# functions to download tweets from API
# input: location and/or time
# output: list of tweets


class DataExtraction:
    def __init__(self, twitter_api):
        self.twitter_api = twitter_api
        pass

    def collect(self, location):
        print("Collecting data for", location["name"])

        return "some data"
