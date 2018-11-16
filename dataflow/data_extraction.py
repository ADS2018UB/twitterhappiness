
# functions to download tweets from API
# input: location and/or time
# output: list of tweets


class DataExtraction:
    def __init__(self, location):
        self.location = location
        pass

    def collect(self, location):
        print("Collecting data for", location["name"])
        return "some data"
