
# functions to download tweets from API
# input: location and/or time
# output: list of tweets


class DataExtraction:
    def __init__(self, twitter_api):
        self.twitter_api = twitter_api
        pass

    def collect(self, location):
        print("Collecting data for", location["name"])

        places = self.twitter_api.reverse_geocode(
            lat=location['lat_center'],
            long=location['lon_center'],
            accuracy=location['radius'])
        place_id = places[0].id
        tweets = self.twitter_api.search(q="place:%s" % place_id, lang='en', count=10)

        return tweets
