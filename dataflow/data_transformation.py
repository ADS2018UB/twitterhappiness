# functions to process downloaded tweets from API
# input: raw tweets
# output: processed tweets (with sentiments and whatever needed)


from textblob import TextBlob
import numpy as np
from pandas.io.json import json_normalize
import pandas as pd
from scipy import stats
from sklearn import cluster
import seaborn as sns
import matplotlib.pyplot as plt
import datetime


def decide_class(sentiment):
    if sentiment <= -0.5:
        return -2
    if sentiment < 0:
        return -1
    if sentiment == 0:
        return 0
    if sentiment < 0.5:
        return 1
    else:
        return 2


# Enhancing 'analize()' to allow 'subjectivity' (see explanation below)
def analyze(data):
    print("Analyzing data: ")

    for elem in data:
        sentiment = TextBlob(elem["text"]).polarity
        elem['sentiment'] = sentiment
        elem['class'] = decide_class(sentiment)
        elem['subjectivity'] = sentiment.subjectivity

        # populate lat, lon fields
        if elem["coordinates"] is not None and elem["coordinates"]["type"] == "Point":
            elem['lat'] = elem["coordinates"]["coordinates"][1]
            elem['lon'] = elem["coordinates"]["coordinates"][0]
        else:
            elem['lat'] = None
            elem['lon'] = None

    return data


###Clustering TextBlob Polarity and TextBlob Subjectivity scores using K-means clustering###

# Subjectivity is based on opinions, i.e. subjectivity scores in texttblob are based on
# keywords like ‘I’, ‘my’, ‘our’, ‘mine’ etc. whereas polarity is based on sentiments whether
# they are positive or negative. Hence by performing clustering on polarity and subjectivity,
# it can be inferred as to how many opinions are positive or negative and the degree of the same.


# Assumes 'data_batch' contains JSON batch of tweets to cluster. Data must have 'subjectivity' element.
# Returns JSON with 'cluster' (0..(K-1)) element added for each tweet

# Future Improvements (in priority):
# 1. add other sentiment analysis libraries such as AFINN, and cluster 'AFINN score' vs. 'TextBlob score'
#     this analysis could help us improve 'decide_class' function. Effectively, tweets with very high degree
#     of positivity in both the tools would be certainly positives (or 'very positives').
# 2. try different 'K' for a given dataset, plot elbow graph and decide optimal K
# 3. try to cluster per 'length  of tweet', 'emojies', others
# 4. try others than KMeans (i.e. Fuzzy C Means, Partitional Clustering)
# 5. take different times of the day to assess mood evolution through the day
# 6. Filter mood according to the topic (hashtag, some KWs, others)

def cluster_tweets(data_batch):
    K = 3  # According to Ahuja et al. (2017) it is the optimal.

    # Since k-means is using euclidean distance, having 'text' element (and 'class') might not be a good idea, not to confuse algorithm

    ##Transforming to Pandas DataFrame with just 'sentiment' and 'subjectivity'
    tweets_proc_pd_norm = json_normalize(data_batch)

    # Leaving 'sentiment' and 'subjectivity' to the data to run KMeans
    tweets_proc_pd_norm_filt = pd.DataFrame(tweets_proc_pd_norm, columns=['sentiment', 'subjectivity'])

    ###Running KMeans
    # Standardize
    clmns = ['sentiment', 'subjectivity']
    tweets_proc_pd_norm_filt_std = stats.zscore(tweets_proc_pd_norm_filt[clmns])

    # Cluster the data
    kmeans = KMeans(n_clusters=3, random_state=0).fit(tweets_proc_pd_norm_filt_std)
    labels = kmeans.labels_

    # Glue back to originaal data
    tweets_proc_pd_norm_filt['clusters'] = labels

    # Add the column into our list
    clmns.extend(['clusters'])

    # Add back cluster to JSON
    i = 0
    for elem in data_batch:
        elem['cluster'] = tweets_proc_pd_norm_filt['clusters'][i]
        i += 1

    ## Lets analyze the clusters
    # Note: Uncomment (delete #) to see results. Comment (add #) to not see results on screen/IO.
    # show_cluster_results(tweets_proc_pd_norm_filt)
    # print(tweets_proc_pd_norm_filt[clmns].groupby(['clusters']).mean())
    # print(tweets_proc_pd_norm_filt)

    return data_batch


# Show clustering results both printed and plotted
def show_cluster_results(tweets_batch):
    sns.lmplot('sentiment', 'subjectivity',
               data=tweets_batch,
               fit_reg=False,
               hue="clusters",
               scatter_kws={"marker": "D",
                            "s": 100})

    plt.title('K-Means results with 3 clusters')
    plt.xlabel('TextBlob Polarity')
    plt.ylabel('TextBlob Subjectivity')

    xmin = -1.1
    xmax = 1.1
    ymin = -0.1
    ymax = 1.1

    axes = plt.gca()
    axes.set_xlim([xmin, xmax])
    axes.set_ylim([ymin, ymax])

    plt.show()
