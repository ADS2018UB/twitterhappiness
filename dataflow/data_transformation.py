
# functions to process downloaded tweets from API
# input: raw tweets
# output: processed tweets (with sentiments and whatever needed)


from textblob import TextBlob


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


def analyze(data):
    print("Analyzing data: ")

    for elem in data:
        sentiment = TextBlob(elem["text"]).polarity
        elem['sentiment'] = sentiment
        elem['class'] = decide_class(sentiment)

    return data
