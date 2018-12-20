
# GENERAL IMPORTS
import os
import textwrap
import datetime
import json
from bson.objectid import ObjectId
import bson
import pandas as pd

# FLASK IMPORTS
from flask import Flask, render_template, make_response, request
from flask_pymongo import PyMongo
from flask import abort, jsonify, redirect, render_template
from flask import request, url_for

# DASH IMPORTS
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_dangerously_set_inner_html
import plotly.graph_objs as go
import pandas as pd
import datetime

# FOLIUM IMPORTS
import folium
from folium.features import CustomIcon
from folium.plugins import HeatMap

# ABOUT US IMPORTS
import tweepy
import datetime as dt
from textblob import TextBlob

# dash_app = dash.Dash(__name__)
# flask_app = dash_app.server

flask_app = Flask(__name__)
dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname='/dashboards/')
dash_app.config.suppress_callback_exceptions = True
dash_app.layout = html.Div()

dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/bootswatch/2.3.2/united/bootstrap.min.css"})
dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-responsive.min.css"})
dash_app.css.append_css({"external_url": "/static/styles/home_page.css"})
dash_app.css.append_css({"external_url": "/static/styles/dashboard.css"})

dash_app.scripts.append_script({"external_url": "https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"})
dash_app.scripts.append_script({"external_url": "/static/scripts/dashboard.js"})


mlab_credentials_file = "../credentials/mlab_credentials.txt"
#DB_TWEETS = "twitter_happiness_test"
DB_TWEETS = "tweets"
DB_LOCATIONS = "twitter_happiness_locations"
DB_UP = False

TWITTER_CREDENTIALS_FILE = "../credentials/twitter_credentials.txt"

with open(TWITTER_CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
    [access_key, access_secret, consumer_key, consumer_secret] = f.read().splitlines()

#Authentication
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

def db_connect():
    global DB_UP
    global MONGO
    global flask_app

    with open(mlab_credentials_file, 'r', encoding='utf-8') as f:
        [name, password, url, dbname] = f.read().splitlines()

    try:
        # db_conn = pymongo.MongoClient("mongodb://{}:{}@{}/{}".format(name, password, url, dbname))
        mongo_url = "mongodb://{}:{}@{}/{}".format(name, password, url, dbname)
        flask_app.config['MONGO_DBNAME'] = dbname
        flask_app.config['MONGO_URI'] = mongo_url
        MONGO = PyMongo(flask_app)
        print("DB connected successfully!!!")
        print("\t", name, url, dbname)
        DB_UP = True

    except:
        print("Could not connect to the DB!")
        flask_app.config['MONGO_DBNAME'] = "dummy_name"
        flask_app.config['MONGO_URI'] = "mongodb://dummy_name:dummy_password@dummy_url/dummy_name"
        MONGO = PyMongo(flask_app)
        DB_UP = False

    return


db_connect()

flask_app.config['SECRET_KEY'] = 'enydM2ANhdcoKwdVa0jWvEsbPFuQpMjf'  # Create your own.
flask_app.config['SESSION_PROTECTION'] = 'strong'

filtered_location = None

DASHBOARD_HEADER_HTML = '''
    <div class="navbar navbar-static-top" >
        <div class="navbar-inner">
            <div class="container">
                <a href="/home/" class="brand nav-link" style="text-shadow: none;">Twitter Happiness</a>
                <ul class="nav">
                    <li><a href="/tweets-list/" class="nav-link" style="text-shadow: none;">Tweets List</a></li>
                    <li><a href="/tweets-map/" class="nav-link" style="text-shadow: none;">Tweets Map</a></li>
                    <li><a href="/tweets-tl/" class="nav-link" style="text-shadow: none;">Tweets TL</a></li>
                    <li><a href="/tweets-celebrity/" class="nav-link" style="text-shadow: none;">Tweets Celebrity</a></li>
                </ul>
                <ul class="nav pull-right">
                    <li><a href="/about-us/" class="nav-link" style="text-shadow: none;">About Us</a></li>
                </ul>
            </div>
        </div>
    </div>
'''
DETAILS = [
    {
        "picture": "alex.jpg",
        "name": "Alex Castrelo",
        "email": "",
        "linkedin": "https://www.linkedin.com/in/alex-castrelo-61b603b4/",
        "github": "https://github.com/Neoares",
    },
    {
        "picture": "gerard.jpg",
        "name": "Gerard Marrugat Torregrosa",
        "email": "gmarrugat@gmail.com",
        "linkedin": "https://www.linkedin.com/in/gerardmarrugat/",
        "github": "https://github.com/gmarrugat",
    },
    {
        "picture": "andreu.jpg",
        "name": "Andreu Masdeu",
        "email": "",
        "linkedin": "https://www.linkedin.com/in/andreu-masdeu-ninot-23139714a/",
        "github": "https://github.com/andreu15",
    },
    {
        "picture": "toni.jpg",
        "name": "Toni Miranda",
        "email": "tmiranda@utexas.edu",
        "linkedin": "https://www.linkedin.com/in/tonimiranda",
        "github": "https://github.com/tmiranda101",
    },
    {
        "picture": "emil.jpg",
        "name": "Emil Nikolov",
        "email": "",
        "linkedin": "",
        "github": "https://github.com/EmilNik",
    },
    {
        "picture": "eduard.jpeg",
        "name": "Eduard Ribas Fernández",
        "email": "edu.ribas.92@gmail.com",
        "linkedin": "https://www.linkedin.com/in/eduardribasfernandez/",
        "github": "https://github.com/kterf",
    },
    {
        "picture": "pilar.jpg",
        "name": "Pilar Santolaria",
        "email": "mpilar.santolaria@gmail.com",
        "linkedin": "https://www.linkedin.com/in/pilarsantolaria/",
        "github": "https://github.com/pilarsantolaria",
    },
]

def dump_request_detail(request):
    request_detail = """
## Request INFO ##
request.endpoint: {request.endpoint}
request.method: {request.method}
request.view_args: {request.view_args}
request.args: {request.args}
request.form: {request.form}
request.user_agent: {request.user_agent}
request.files: {request.files}
request.is_xhr: {request.is_xhr}

## request.headers ##
{request.headers}
    """.format(request=request).strip()
    return request_detail


@flask_app.before_request
def callme_before_every_request():
    # Demo only: the before_request hook.
    flask_app.logger.debug('# Before Request #\n')
    flask_app.logger.debug(dump_request_detail(request))


@flask_app.after_request
def callme_after_every_response(response):
    # Demo only: the after_request hook.
    flask_app.logger.debug('# After Request #\n' + repr(response))
    return response


@flask_app.errorhandler(404)
def error_not_found(error):
    return render_template('error/not_found.html'), 404


@flask_app.errorhandler(bson.errors.InvalidId)
def error_not_found(error):
    return render_template('error/not_found.html'), 404


@flask_app.route('/')
def index():
    # return render_template('index.html')
    return redirect(url_for('home_page'))


@flask_app.route('/home/')
def home_page():
    locations = [location["name"] for location in MONGO.db[DB_LOCATIONS].find().sort("name")]
    return render_template('home/home_page.html', locations=locations)

@flask_app.route('/tweets-celebrity/')
def tweets_celebrity():
    locations = [location["name"] for location in MONGO.db[DB_LOCATIONS].find().sort("name")]
    return render_template('tweets/cel_page.html', locations=locations)

@flask_app.route('/tweets-list/')
def tweets_list():
    """Provide HTML listing of all Tweets."""
    tweets = MONGO.db[DB_TWEETS].find()[:30]
    return render_template('tweets/list.html', tweets=tweets)


@flask_app.route('/about-us/')
def about_us():
    return render_template('about_us/about_us.html', details=DETAILS)




@flask_app.route('/tweets-tl/')
def tweets_tl():
    global dash_app

    locations = [loc for loc in MONGO.db[DB_LOCATIONS].find().sort("name")]

    location = None
    try:
        location = request.args['location']
    except:
        pass
    if location == None:
        location = locations[0]["name"]
    print(location)

    days_history = 6
    days_markers = {}
    for i in range(-days_history, 1):
        days_markers[i] = datetime.datetime.strftime(datetime.datetime.today() + datetime.timedelta(days=i), "%d-%m-%Y")

    dash_app.layout = html.Div([

        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(DASHBOARD_HEADER_HTML)
        ]),

        html.Div([

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),
            ## multi=True
            html.Div([
                dcc.Dropdown(
                    id='locations-filter-tl',
                    options=[{'label': loc["name"], 'value': loc["name"]} for loc in locations],
                    value=location
                )], style={'width': '50%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                dcc.RangeSlider(
                    id='date-slider-tl',
                    min=-days_history,
                    max=0,
                    marks=days_markers,
                    value=[-days_history, 0]
                )], style={'width': '80%', 'margin': 'auto'}),

             html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

            html.Div([
                html.Div(dcc.Graph(id='tweets-tl'), style={'width': '75%', 'margin':'auto'}),
                html.Div(style={'width': '100%', 'display': 'inline-block'})

            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '150px'}),
        ],
            style={'width': '80%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()


def select_image(mean):
    if mean > 0.05:
        return 'static/icon_happy.png'
    if mean < -0.05:
        return 'static/icon_sad.png'
    else: return 'static/icon_neutral.png'


@dash_app.callback(
    dash.dependencies.Output('tweets-tl', 'figure'),
    [
        dash.dependencies.Input('locations-filter-tl', 'value'),
        dash.dependencies.Input('date-slider-tl', 'value')
    ]
)
def update_tweets_tl(location_filter, date_filter):
    root_url = request.url_root

    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    # print(location)

    min_day = datetime.datetime.today().replace(hour=00, minute=00, second=00) + datetime.timedelta(days=date_filter[0])
    max_day = datetime.datetime.today().replace(hour=23, minute=59, second=59) + datetime.timedelta(days=date_filter[1])

    location_query = {
        "lat": {
            "$gt": location["lat_min"],
            "$lt": location["lat_max"]
        },
        "lon": {
            "$gt": location["lon_min"],
            "$lt": location["lon_max"]
        },
        "datetime": {
            "$gte": min_day,
            "$lte": max_day,
        }
    }
    tweets = MONGO.db[DB_TWEETS].find(location_query)[:300]

    classes = []
    classes_categ = []
    dicc_classes = {-2: 'Very Negative', -1: 'Negative', 0: 'Neutral',
    1: 'Positive', 2:'Very Positive'}
    nb_tweets = 0
    for tweet in tweets:
        classes.append(tweet["class"])
        classes_categ.append(dicc_classes[tweet['class']])
        nb_tweets += 1

    y = [1,1,1,1,1]
    for category in classes:
        y[category+2] +=1

    try:
        mean = sum(classes)/nb_tweets
    except: mean = 0
    print(y)
    data = [

    go.Histogram(
    y = y,
    histfunc = "sum",
    x = ['Very Negative',  'Negative', 'Neutral',
     'Positive','Very Positive'],

     histnorm='probability',
     marker=dict(
        color=['rgba(219, 29, 0,1)', 'rgba(255, 96, 61,1)',
               'rgba(245,255,20,1)', 'rgba(86, 244, 66,1)',
               'rgba(4, 160, 4,1)'])
    )
    ]

    layout = go.Layout(
    title='Sentiment in {}'.format(location_filter),

    yaxis=dict(
        title='% of tweets'
    ),
    bargap=0.2,
    bargroupgap=0.1,
    images=[dict(
        source=root_url+select_image(mean),
        xref="paper", yref="paper",
        x=0.825, y=1.1,
        sizex=0.25, sizey=0.25,
        xanchor="right", yanchor="bottom"
      )]
    )
    # we add a scatter trace with data points in opposite corners to give the Autoscale feature a reference point



    hist1 = dict(data=data, layout=layout)


    return hist1

initial_img = 'https://i.guim.co.uk/img/media/acb1627786c251362c4bc87c1f53fa39b49d8d3d/0_0_1368_1026/master/1368.jpg?width=300&quality=85&auto=format&fit=max&s=257a6abd5fef974f53e7b81dd81937da'

def celebrity_tracking(user_name, n): #n is the number of tweets to be retrieved,

    user = api.get_user(screen_name = user_name)
    juser = user._json
    img_url = juser['profile_image_url']

    query = "from:"+user_name+"/-filter:retweets"
    tweets = api.search(q=query, count=n)
    tweets_json = []
    sentiments = []
    for tweet in tweets:
        tweets_json.append(tweet._json)
        sentiment = TextBlob(tweet._json['text']).polarity
        sentiments.append(sentiment)
    return (img_url,tweets_json, sentiments)

@flask_app.route('/tweets-user/')
def tweets_user():
    global dash_app

    try:
        user = request.args['User ID']
    except:
        pass

    users = [ user,
    '@justinbieber',
    '@katyperry',
	'@BarackObama',
    '@rihanna',
    '@ladygaga',
	'@TheEllenShow',
    '@jtimberlake',
    '@ArianaGrande',
    '@KimKardashian',
    '@selenagomez',
    '@ddlovato',
    '@britneyspears',
    '@realDonaldTrump',
    ]

    initial_img = 'https://i.guim.co.uk/img/media/acb1627786c251362c4bc87c1f53fa39b49d8d3d/0_0_1368_1026/master/1368.jpg?width=300&quality=85&auto=format&fit=max&s=257a6abd5fef974f53e7b81dd81937da'
    dash_app.layout = html.Div([

        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(DASHBOARD_HEADER_HTML)
        ]),

        html.Div([

        html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

        html.Div([
            ## multi=True
            html.Div([

            html.Div([
                dcc.Dropdown(
                    id='user-filter',
                    options=[{'label': user2, 'value': user2} for user2 in users ],
                    value=user
                )], style={'width': '50%', 'margin': 'auto'})]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'})]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                html.Div(style={'width': '15%', 'display': 'inline-block'}),
                html.Div(
                html.Img(id='img-user', src=initial_img, height='270', width='270'), style={ 'display': 'inline-block',  'vertical-align':'top'}),
                html.Div(dcc.Graph(id='tweets-user-stats'), style={'width': '45%', 'display': 'inline-block'}),
                html.Div(style={'width': '15%', 'display': 'inline-block'})
                            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                html.Div(style={'width': '15%', 'display': 'inline-block'}),
                html.Div(dcc.Graph(id='tweets-user'), style={'width': '45%', 'display': 'inline-block'}),
                html.Div(style={'width': '3%', 'display': 'inline-block'}),
                html.Div(id='tweets-list2', style={'width': '25%', 'display': 'inline-block', 'vertical-align':'top', 'overflow':'auto', 'max-height': '440px'}),
                html.Div(style={'width': '15%', 'display': 'inline-block'})
            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '150px'}),
        ],
            style={'width': '80%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()

@dash_app.callback(
    dash.dependencies.Output('tweets-user', 'figure'),
    [dash.dependencies.Input('user-filter', 'value')]
)
def update_tweets_user(user_filter):
    root_url = request.url_root

    try:
        profile_img_url, tweets, sentiments = celebrity_tracking(user_filter, 30)

    except:
         pass

    y = [0.01,0.01,0.01,0.01,0.01]


    try:
        mean = sum(sentiments)/len(sentiments)
        for elem in sentiments:
            if elem > 0.5:
                y[4] += 1
            elif elem > 0.05:
                y[3] += 1
            elif elem > -0.05:
                y[2] += 1
            elif elem > -0.5:
                y[1] += 1
            else: y[0] += 1

    except:
        mean = 0

    print(y)
    data = [

    go.Histogram(
    y = y,
    histfunc = "sum",
    x = ['Very Negative',  'Negative', 'Neutral',
     'Positive','Very Positive'],

     histnorm='probability',
     marker=dict(
        color=['rgba(219, 29, 0,1)', 'rgba(255, 96, 61,1)',
               'rgba(245,255,20,1)', 'rgba(86, 244, 66,1)',
               'rgba(4, 160, 4,1)'])
    )
    ]


    layout = go.Layout(


    yaxis=dict(
        title='% of tweets'
    ),
    bargap=0.2,
    bargroupgap=0.1,
    images=[dict(
        source=root_url+select_image(mean),
        xref="paper", yref="paper",
        x=0.5, y=1.1,
        sizex=0.25, sizey=0.25,
        xanchor="center", yanchor="bottom"
      )]
    )
    # we add a scatter trace with data points in opposite corners to give the Autoscale feature a reference point



    hist1 = dict(data=data, layout=layout)


    return hist1
# DASHBOARD COMPONENTS
def transform_str(nb):
    if nb > 1000000:

        str_nb = str(nb)[:-5]
        if str_nb[-1] == '0': return str_nb[0:-1]+' M'
        else: return str_nb[0:-1]+',' + str_nb[-1] + ' M'

    elif nb > 1000:

        str_nb = str(nb)[:-2]
        if str_nb[-1] == '0': return str_nb[0:-1]+' k'
        else: return str_nb[0:-1]+',' + str_nb[-1] + ' k'

    else:
        return nb

@dash_app.callback(
    dash.dependencies.Output('tweets-user-stats', 'figure'),
    [dash.dependencies.Input('user-filter', 'value')]
)
def update_stats_user(user_filter):
    root_url = request.url_root

    try:
        user = api.get_user(screen_name = user_filter)
        tweet_count = transform_str(user.statuses_count)
        follower_count = transform_str(user.followers_count)
        following_count = transform_str(user.friends_count)
    except:
         tweet_count = 0
         follower_count = 0
         following_count = 0

    trace = go.Table(
    columnorder = [1,2,3],
    columnwidth = [1000,1000, 1000],
    header=dict(values=['Tweets', 'Followers', 'Following'],
                line = dict(color='#609dff'),
                fill = dict(color='#609dff'),
                align = ['center'], height=40,
               font = dict(color = 'black', size = 21)),
    cells=dict(values=[[tweet_count, ''],
                       [follower_count],
                          [following_count]],
               line = dict(color='#609dff'),
               fill = dict(color='#609dff'),
               align = ['center'],
              font = dict(color = 'white', size = 30),
                    height=35))

    layout = dict(width=700, height=270 ,paper_bgcolor='rgba(96, 157, 255, 1)',
    plot_bgcolor='rgba(96, 157, 255, 1)')
    data=[trace]
    table1 = dict(data=data, layout=layout)

    return table1

@dash_app.callback(
    dash.dependencies.Output('img-user', 'src'),
    [dash.dependencies.Input('user-filter', 'value')]
)
def update_img_user(user_filter):
    root_url = request.url_root

    try:
        #user = api.get_user(screen_name = user_filter)
        #juser = user._json
        #img_url = juser['profile_image_url']
        img_url = 'http://avatars.io/twitter/'+user_filter[1:]
    except:
         img_url = initial_img

    print(img_url)
    return img_url

def select_class(sentim):
    if sentim > 0.5:
        return 2
    elif sentim > 0.05:
        return 1
    elif sentim > -0.05:
        return 0
    elif sentim > -0.5:
        return -1
    else: return -2


@dash_app.callback(
    dash.dependencies.Output('tweets-list2', 'children'),
    [
        dash.dependencies.Input('user-filter', 'value')
    ]
)
def update_tweets_list2(user_filter):

    try:
        profile_img_url, tweets, sentiments = celebrity_tracking(user_filter, 30)

    except:

         tweets = []

    #tweets_list = [tweet for tweet in tweets]
    #html_content = '<div class="tweets-scrolling-box" > '
    html_content = ''
    for kk, tweet in enumerate(tweets):
        tweet['class'] = select_class(sentiments[kk])
        html_content += '<div id="' + tweet["id_str"] +'"class="tweet" style="background-color:' + sentiment_class_colors[tweet["class"]] + '";>' + tweet['text'] + "<br><i>"  + "</i>" + '</div>'
    #html_content = ''.join([html_content, '</div>'])

    content = dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html_content)
    return content



ICON_SIZE = 20

def select_custom_emoji(root_url, sentiment):
    # https://emojipedia.org/whatsapp/
    if sentiment == -2:
        return folium.features.CustomIcon(root_url+"static/emoji_-2.png", icon_size=(ICON_SIZE, ICON_SIZE))
    elif sentiment == -1:
        return folium.features.CustomIcon(root_url +"static/emoji_-1.png", icon_size=(ICON_SIZE, ICON_SIZE))
    elif sentiment == 1:
        return folium.features.CustomIcon(root_url +"static/emoji_1.png", icon_size=(ICON_SIZE, ICON_SIZE))
    elif sentiment == 2:
        return folium.features.CustomIcon(root_url +"static/emoji_2.png", icon_size=(ICON_SIZE, ICON_SIZE))
    else:
        return folium.features.CustomIcon(root_url + "static/emoji_0.png", icon_size=(ICON_SIZE, ICON_SIZE))


def select_custom_icon(root_url, sentiment):
    if sentiment < 0:
        return folium.features.CustomIcon(root_url+"static/icon_sad.png", icon_size=(ICON_SIZE, ICON_SIZE))
    elif sentiment > 0:
        return folium.features.CustomIcon(root_url+"static/icon_happy.png", icon_size=(ICON_SIZE, ICON_SIZE))
    else:
        return folium.features.CustomIcon(root_url+"static/icon_neutral.png", icon_size=(ICON_SIZE, ICON_SIZE))


def select_custom_twitter(root_url, sentiment):
    if sentiment < 0:
        return folium.features.CustomIcon(root_url+"static/twitter_sad.png", icon_size=(ICON_SIZE, ICON_SIZE))
    elif sentiment > 0:
        return folium.features.CustomIcon(root_url+"static/twitter_happy.png", icon_size=(ICON_SIZE, ICON_SIZE))
    else:
        return folium.features.CustomIcon(root_url+"static/twitter_neutral.png", icon_size=(ICON_SIZE, ICON_SIZE))


sentiment_class_colors = {
        -2: "rgb(255, 0, 0)",
        -1: "rgb(255, 102, 0)",
        0: "rgb(255, 255, 0)",
        1: "rgb(153, 255, 51)",
        2: "rgb(0, 255, 0)",
    }

def decide_class_subjectivity(subjectivity):
    if subjectivity <= 0.33:
        return -2
    if subjectivity < 0.66:
        return 0
    else:
        return 2


@flask_app.route('/tweets-map/')
def tweets_map():
    global dash_app

    locations = [loc for loc in MONGO.db[DB_LOCATIONS].find().sort("name")]

    location = None
    try:
        location = request.args['location']
    except:
        pass
    if location is None:
        location = locations[0]["name"]
    #print(location)

    days_history = 6
    days_markers = {}
    for i in range(-days_history, 1):
        days_markers[i] = datetime.datetime.strftime(datetime.datetime.today() + datetime.timedelta(days=i), "%d-%m-%Y")

    dash_app.layout = html.Div([

        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(DASHBOARD_HEADER_HTML)
        ]),

        html.Div([

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([

                html.Div([
                    dcc.Dropdown(
                        id='locations-filter',
                        options=[{'label': loc["name"], 'value': loc["name"]} for loc in locations],
                        value=location
                    ),
                ], style={'width': '50%', 'margin': 'auto'}
                ),  # 'margin': 'auto'}),

                html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

                html.Div([

                    html.Div([
                        dcc.Textarea(
                            id='hashtag-filter',
                            placeholder='Hashtag...',
                            value='',
                            style={'width': '100%', 'height': '30px'}
                        )], style={'width': '40%', 'height': '30px', 'margin': 'auto', 'display': 'inline-block'}
                    ),

                    html.Div([
                        dcc.RadioItems(
                            id='map-type',
                            options=[{'label': ' ' + i, 'value': i} for i in
                                     ['Circles', 'Icons', 'Heatmap', 'Subjectivity']],
                            value='Circles',
                            labelStyle={'display': 'inline-block', 'margin-left': '10px', 'margin-right': '10px',
                                        'word-spacing': '5px'}
                        )], style={'margin-left': '20px', 'display': 'inline-block', 'vertical-align': 'top', 'float': 'right'}

                    ),

                ], style={'width': '80%', 'margin': 'auto'}),

                html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

                html.Div([
                    dcc.RangeSlider(
                        id='date-slider',
                        min=-days_history,
                        max=0,
                        marks=days_markers,
                        value=[-days_history, 0],
                        #value=[-5, -3]
                    )], style={'width': '100%', 'margin': 'auto'}
                ),
            ], id='filters-menu', style={'width': '70%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

            html.Div([
                html.Div(id='tweets-map', style={'width': '65%', 'display': 'inline-block'}),
                html.Div(style={'width': '3%', 'display': 'inline-block'}),
                html.Div(id='tweets-list', style={'width': '30%', 'display': 'inline-block'})
            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div(id='selected-tweet'),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),
        ],
            style={'width': '90%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()


@dash_app.callback(
    dash.dependencies.Output('tweets-list', 'children'),
    [
        dash.dependencies.Input('locations-filter', 'value'),
        dash.dependencies.Input('map-type', 'value'),
        dash.dependencies.Input('hashtag-filter', 'value'),
        dash.dependencies.Input('date-slider', 'value'),

    ]
)
def update_tweets_list(location_filter, map_type, hashtag_filter, date_filter):

    min_day = datetime.datetime.today().replace(hour=00, minute=00, second=00) + datetime.timedelta(days=date_filter[0])
    max_day = datetime.datetime.today().replace(hour=23, minute=59, second=59) + datetime.timedelta(days=date_filter[1])
    #print(min_day, ' - ', max_day)

    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    #print(location)

    query = {
        "lat": {
            "$gte": location["lat_min"],
            "$lte": location["lat_max"]
        },
        "lon": {
            "$gte": location["lon_min"],
            "$lte": location["lon_max"]
        },
        "datetime": {
            "$gte": min_day,
            "$lte": max_day,
        }
    }

    if hashtag_filter != '':
        query["entities.hashtags"] = {
            "$elemMatch": {
                "text": {
                    "$regex": "^" + hashtag_filter + "$",
                    "$options": "i"
                }
            }
        }

    tweets = MONGO.db[DB_TWEETS].find(query)  # [:300]

    if map_type == 'Subjectivity':
        html_content = ''
        for tweet in tweets:
            # {white-space: pre-line;}
            html_content += '<div id="' + tweet["id_str"] +'"class="tweet" style="background-color:' + sentiment_class_colors[decide_class_subjectivity(tweet["subjectivity"])] + '";>' + tweet['text'] + "<br><i>" + datetime.datetime.strftime(tweet['datetime'], "%d-%m-%Y %H:%M") + "</i>" + '</div>'
        #html_content = ''.join([html_content, '</div>'])
    else:
        html_content = ''
        for tweet in tweets:
            # {white-space: pre-line;}
            html_content += '<div id="' + tweet["id_str"] +'"class="tweet" style="background-color:' + sentiment_class_colors[tweet["class"]] + '";>' + tweet['text'] + "<br><i>" + datetime.datetime.strftime(tweet['datetime'], "%d-%m-%Y %H:%M") + "</i>" + '</div>'
        #html_content = ''.join([html_content, '</div>'])

    content = dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html_content)
    return content


@dash_app.callback(
    dash.dependencies.Output('tweets-map', 'children'),
    [
        dash.dependencies.Input('locations-filter', 'value'),
        dash.dependencies.Input('map-type', 'value'),
        dash.dependencies.Input('hashtag-filter', 'value'),
        dash.dependencies.Input('date-slider', 'value')
    ]
)
def update_tweets_map(location_filter, map_type, hashtag_filter, date_filter):
    root_url = request.url_root

    mapbox_access_token = 'pk.eyJ1IjoiZWR1cmYiLCJhIjoiY2pvOTg2NWFjMDd0MjN2b2pveXcxam1taCJ9.1vQR8y_zH5YsUkbJbdOjaw'

    min_day = datetime.datetime.today().replace(hour=00, minute=00, second=00) + datetime.timedelta(days=date_filter[0])
    max_day = datetime.datetime.today().replace(hour=23, minute=59, second=59) + datetime.timedelta(days=date_filter[1])
    #print(min_day, ' - ', max_day)

    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    #print(location)

    query = {
        "lat": {
            "$gte": location["lat_min"],
            "$lte": location["lat_max"]
        },
        "lon": {
            "$gte": location["lon_min"],
            "$lte": location["lon_max"]
        },
        "datetime": {
            "$gte": min_day,
            "$lte": max_day,
        }
    }

    if hashtag_filter != '':
        query["entities.hashtags"] = {
            "$elemMatch": {
                "text": {
                    "$regex": "^" + hashtag_filter + "$",
                    "$options": "i"
                }
            }
        }

    tweets = MONGO.db[DB_TWEETS].find(query)

    if map_type == 'Circles':
        tweets_ids = []
        tweets_lats = []
        tweets_lons = []
        tweets_texts = []
        tweets_colors = []
        for tweet in tweets:
            tweets_ids.append(tweet["id_str"])
            tweets_lats.append(tweet["lat"])
            tweets_lons.append(tweet["lon"])
            tweets_texts.append(
                "<br>".join(textwrap.wrap(tweet["text"], 50)) + "<br><i>" + datetime.datetime.strftime(tweet['datetime'], "%d-%m-%Y %H:%M") + "</i>"
            )
            tweets_colors.append(sentiment_class_colors[tweet["class"]])

        data = [
            go.Scattermapbox(
                customdata=tweets_ids,
                lat=tweets_lats,
                lon=tweets_lons,
                mode='markers',
                marker=dict(
                    # symbol="square",
                    size=14,
                    color=tweets_colors,
                ),
                text=tweets_texts,
                hoverinfo='text'  # 'name + x + y + text',
            )
        ]

        layout = go.Layout(
            autosize=True,
            height=600,
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=location["lat_center"],
                    lon=location["lon_center"]
                ),
                pitch=0,
                zoom=10
            ),
            margin={
                'l': 0,
                'r': 0,
                'b': 0,
                't': 0
            },
        )

        return dcc.Graph(id="tweets-map-circle", figure=go.Figure(data=data, layout=layout))


    if map_type == 'Subjectivity':
        tweets_ids = []
        tweets_lats = []
        tweets_lons = []
        tweets_texts = []
        tweets_colors = []
        for tweet in tweets:
            tweets_ids.append(tweet["id_str"])
            tweets_lats.append(tweet["lat"])
            tweets_lons.append(tweet["lon"])
            tweets_texts.append(
                "<br>".join(textwrap.wrap(tweet["text"], 50)) + "<br><i>" + datetime.datetime.strftime(
                    tweet['datetime'], "%d-%m-%Y %H:%M") + "</i>"
            )
            tweets_colors.append(sentiment_class_colors[decide_class_subjectivity(tweet["subjectivity"])])

        data = [
            go.Scattermapbox(
                customdata=tweets_ids,
                lat=tweets_lats,
                lon=tweets_lons,
                mode='markers',
                marker=dict(
                    # symbol="square",
                    size=14,
                    color=tweets_colors,
                ),
                text=tweets_texts,
                hoverinfo='text'  # 'name + x + y + text',
            )
        ]

        layout = go.Layout(
            autosize=True,
            height=600,
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=location["lat_center"],
                    lon=location["lon_center"]
                ),
                pitch=0,
                zoom=10
            ),
            margin={
                'l': 0,
                'r': 0,
                'b': 0,
                't': 0
            },
        )

        return dcc.Graph(id="tweets-map-circle", figure=go.Figure(data=data, layout=layout))


    if map_type == 'Icons':
        m = folium.Map(
            location=[location["lat_center"], location["lon_center"]],
            tiles='CartoDB positron',  # 'CartoDB dark_matter', 'OpenStreetMap'
            zoom_start=12
        )
        for tweet in tweets:
            m.add_child(folium.Marker(
                location=[tweet['lat'], tweet['lon']],
                #icon=select_custom_emoji(root_url, tweet["class"]),
                #icon = select_custom_icon(root_url, tweet["class"]),
                icon=select_custom_twitter(root_url, tweet["class"]),
                popup=folium.Popup(tweet['text'])
            ))
        #m.save('maps/map_emojis.html')
        map_html = m.get_root().render()
        return html.Iframe(id='tweets-map-icons', srcDoc=map_html, width='100%', height='600')

    if map_type == 'Heatmap':
        data = [[tweet['lat'], tweet['lon'], tweet["class"]] for tweet in tweets]
        m = folium.Map(
            # http://python-visualization.github.io/folium/docs-v0.5.0/plugins.html
            location=[location["lat_center"], location["lon_center"]],
            tiles='CartoDB positron',  # 'stamentoner',
            zoom_start=12
        )
        HeatMap(data).add_to(m)
        #m.save('maps/map_heatmap.html')
        map_html = m.get_root().render()
        return html.Iframe(id='tweets-map-heatmap', srcDoc=map_html, width='100%', height='600')

    return


@dash_app.callback(
    dash.dependencies.Output('selected-tweet', 'children'),
    [
        dash.dependencies.Input('tweets-map-circle', 'hoverData')
    ]
)
def map_data_hover(hover_point):
    if hover_point is None:
        return
    hover_tweet_id = hover_point['points'][0]["customdata"]
    return hover_tweet_id


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(conflict_handler='resolve')

    parser.add_argument('--host', '-h', help='Host (IP)', type=str, default='0.0.0.0')
    parser.add_argument('--port', '-p', help='Port', type=str, default='80')

    args = parser.parse_args()

    flask_app.run(host=args.host, port=args.port)
    # dash_app.run_server()
