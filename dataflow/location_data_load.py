
# load into the DB the list of locations to consider in the app

from db_connection import connect


# define list of locations to be considered
# https://boundingbox.klokantech.com
locations = [
    {
        "name": "New York",
        "box": [-74.5236,40.4938,-73.4606,40.9642]
    },
    {
        "name": "Washington",
        "box": [-77.2308,38.7807,-76.8609,39.0545]
    },
    {
        "name": "Los Angeles",
        "box": [-118.9517,33.5604,-116.8706,34.5165]
    },
    {
        "name": "Chicago",
        "box": [-88.0823,41.5492,-87.2591,42.4069]
    },
    {
        "name": "Houston",
        "box": [-95.6408,29.5606,-95.0819,29.9616]
    },
    {
        "name": "Boston",
        "box": [-71.166074,42.29945,-70.948637,42.445808]
    },
    {
        "name": "Sydney",
        "box": [150.9334,-34.0594,151.4074,-33.5574]
    },
    {
        "name": "Ottawa",
        "box": [-76.009138,45.265278,-75.349687,45.584893]
    },
    {
        "name": "Toronto",
        "box": [-79.7194,43.5093,-79.0599,43.8387]
    },
    {
        "name": "Montreal",
        "box": [-73.9651,45.392,-73.3057,45.7109]
    },
    #{
    #    "name": "Barcelona",
    #    "box": [2.03,41.2845,2.3184,41.4958]
    #},
    #{
    #    "name": "Madrid",
    #    "box": [-3.887581,40.328514,-3.516543,40.518785]
    #},
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