
from tweepy import Stream, StreamListener,OAuthHandler
import json



TWITTER_CREDENTIALS_FILE = '..credentials/twitter_credentials.txt'

def get_tweets(location, max_tweets):

    loc = location    
    max_tweets = max_tweets
    tweets = []
    
    #1. Create a class inheriting from StreamListener
    #1.1. Authentication
    #2. Using that class create a Stream object
    #3. Connect to the Twitter API using the Stream.

    #1
    class listener(StreamListener):
    
        def __init__(self):
            super(StreamListener, self).__init__()
            self.num_tweets = 0
        def on_data(self, data):
            #Beauty print data
            if self.num_tweets < max_tweets:
                parsed = json.loads(data)
                #print (json.dumps(parsed, indent=4, sort_keys=True))
                tweets.append(parsed)
                self.num_tweets += 1
                return True
            else:
                return False

        def on_error(self, status_code):
            if status_code == 420:
                #returning False in on_data disconnects the stream
                return False

    
#1.1

    with open(TWITTER_CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
        [access_key, access_secret, consumer_key, consumer_secret] = f.read().splitlines()

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)

#2.
    twitterStream = Stream(auth, listener()) 

#3.
    twitterStream.filter(locations=loc)
    
    return(tweets)