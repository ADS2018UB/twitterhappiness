
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

# FOLIUM IMPORTS
import folium
from folium.features import CustomIcon
from folium.plugins import HeatMap


# dash_app = dash.Dash(__name__)
# flask_app = dash_app.server

flask_app = Flask(__name__)
dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname='/dashboards')
dash_app.config.suppress_callback_exceptions = True
dash_app.layout = html.Div()
dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/bootswatch/2.3.2/united/bootstrap.min.css"})
dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-responsive.min.css"})
dash_app.css.append_css({"external_url": "/static/styles/dashboard.css"})

mlab_credentials_file = "../credentials/mlab_credentials.txt"
#DB_TWEETS = "twitter_happiness_test"
DB_TWEETS = "tweets"
DB_LOCATIONS = "twitter_happiness_locations"
DB_UP = False


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


@flask_app.route('/tweets-list/')
def tweets_list():
    """Provide HTML listing of all Tweets."""
    tweets = MONGO.db[DB_TWEETS].find()[:30]
    return render_template('tweets/list.html', tweets=tweets)


@flask_app.route('/about-us/')
def about_us():
    """Provide HTML listing of all Tweets."""
    tweets = MONGO.db[DB_TWEETS].find()[50:60]
    return render_template('tweets/list.html', tweets=tweets)


def select_custom_emoji(root_url, sentiment):
    # https://emojipedia.org/whatsapp/
    if sentiment == -2:
        return folium.features.CustomIcon(root_url+"static/emoji_-2.png", icon_size=(15, 15))
    elif sentiment == -1:
        return folium.features.CustomIcon(root_url +"static/emoji_-1.png", icon_size=(15, 15))
    elif sentiment == 1:
        return folium.features.CustomIcon(root_url +"static/emoji_1.png", icon_size=(15, 15))
    elif sentiment == 2:
        return folium.features.CustomIcon(root_url +"static/emoji_2.png", icon_size=(15, 15))
    else:
        return folium.features.CustomIcon(root_url + "static/emoji_0.png", icon_size=(15, 15))


def select_custom_icon(root_url, sentiment):
    if sentiment < 0:
        return folium.features.CustomIcon(root_url+"static/icon_sad.png", icon_size=(15, 15))
    elif sentiment > 0:
        return folium.features.CustomIcon(root_url+"static/icon_happy.png", icon_size=(15, 15))
    else:
        return folium.features.CustomIcon(root_url+"static/icon_neutral.png", icon_size=(15, 15))


@flask_app.route('/tweets-map-icons/')
def tweets_map_icons():
    root_url = request.url_root

    location = MONGO.db[DB_LOCATIONS].find({"name": "Barcelona"})[0]
    location_query = {
        "lat": {
            "$gt": location["lat_min"],
            "$lt": location["lat_max"]
        },
        "lon": {
            "$gt": location["lon_min"],
            "$lt": location["lon_max"]
        }
    }

    tweets = MONGO.db[DB_TWEETS].find(location_query)[:100]
    tweets = [tweet for tweet in tweets]

    m = folium.Map(
        location=[location["lat_center"], location["lon_center"]],
        tiles='CartoDB positron',  # 'CartoDB dark_matter', 'OpenStreetMap'
        zoom_start=12
    )

    for tweet in tweets:
        m.add_child(folium.Marker(
            location=[tweet['lat'], tweet['lon']],
            #icon=select_custom_emoji(root_url, tweet["class"]),
            icon=select_custom_icon(root_url, tweet["class"]),
            popup=folium.Popup(tweet['text'])
        ))

    m.save('maps/map_icons.html')
    #with open('map.html') as f:
    #    map_html = f.read()
    #print(map_html)
    map_html = m.get_root().render()

    dash_app.layout = html.Div([

        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
                    <div class="navbar navbar-static-top" >
                    <div class="navbar-inner" style="background-image: none !important; background-color: rgb(29, 161, 242); !important; border: none !important">
                        <div class="container">
                            <a href="/home/" class="brand" style="text-shadow: none;">Twitter Happiness</a>
                            <ul class="nav">
                                <li><a href="/tweets-list/" style="text-shadow: none;">Tweets List</a></li>
                                <li><a href="/tweets-map/" style="text-shadow: none;">Tweets Map</a></li>                            
                            </ul>
                            <ul class="nav pull-right">
                                <li><a href="/about-us/" style="text-shadow: none;">About Us</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
                ''')
        ]),

        html.Div([

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                dcc.RangeSlider(
                    id='date-slider',
                    min=-5,
                    max=0,
                    value=[-5, 0]
                )], style={'width': '80%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Iframe(id='map', srcDoc=map_html, width='100%', height='600'), # open('map.html', 'r').read()

            #dash_dangerously_set_inner_html.DangerouslySetInnerHTML(map_html)
        ],
            style={'width': '80%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()


@flask_app.route('/tweets-map-emojis/')
def tweets_map_emojis():
    root_url = request.url_root

    location = MONGO.db[DB_LOCATIONS].find({"name": "Barcelona"})[0]
    location_query = {
        "lat": {
            "$gt": location["lat_min"],
            "$lt": location["lat_max"]
        },
        "lon": {
            "$gt": location["lon_min"],
            "$lt": location["lon_max"]
        }
    }

    tweets = MONGO.db[DB_TWEETS].find(location_query)[:100]
    tweets = [tweet for tweet in tweets]

    m = folium.Map(
        location=[location["lat_center"], location["lon_center"]],
        tiles='CartoDB positron',  # 'CartoDB dark_matter', 'OpenStreetMap'
        zoom_start=12
    )

    for tweet in tweets:
        m.add_child(folium.Marker(
            location=[tweet['lat'], tweet['lon']],
            icon=select_custom_emoji(root_url, tweet["class"]),
            popup=folium.Popup(tweet['text'])
        ))

    m.save('maps/map_emojis.html')
    #with open('map.html') as f:
    #    map_html = f.read()
    #print(map_html)
    map_html = m.get_root().render()

    dash_app.layout = html.Div([

        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
                    <div class="navbar navbar-static-top" >
                    <div class="navbar-inner" style="background-image: none !important; background-color: rgb(29, 161, 242); !important; border: none !important">
                        <div class="container">
                            <a href="/home/" class="brand" style="text-shadow: none;">Twitter Happiness</a>
                            <ul class="nav">
                                <li><a href="/tweets-list/" style="text-shadow: none;">Tweets List</a></li>
                                <li><a href="/tweets-map/" style="text-shadow: none;">Tweets Map</a></li>                            
                            </ul>
                            <ul class="nav pull-right">
                                <li><a href="/about-us/" style="text-shadow: none;">About Us</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
                ''')
        ]),

        html.Div([

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                dcc.RangeSlider(
                    id='date-slider',
                    min=-5,
                    max=0,
                    value=[-5, 0]
                )], style={'width': '80%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Iframe(id='map', srcDoc=map_html, width='100%', height='600'), # open('map.html', 'r').read()

            #dash_dangerously_set_inner_html.DangerouslySetInnerHTML(map_html)
        ],
            style={'width': '80%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()


@flask_app.route('/tweets-map-heatmap/')
def tweets_map_heatmap():

    location = MONGO.db[DB_LOCATIONS].find({"name": "Barcelona"})[0]
    location_query = {
        "lat": {
            "$gt": location["lat_min"],
            "$lt": location["lat_max"]
        },
        "lon": {
            "$gt": location["lon_min"],
            "$lt": location["lon_max"]
        }
    }

    tweets = MONGO.db[DB_TWEETS].find(location_query)[:100]
    data = [[tweet['lat'],tweet['lon'],tweet["class"]] for tweet in tweets]

    m = folium.Map(
        # http://python-visualization.github.io/folium/docs-v0.5.0/plugins.html
        location=[location["lat_center"], location["lon_center"]],
        tiles='CartoDB positron', #'stamentoner',
        zoom_start=12
    )

    HeatMap(data).add_to(m)

    m.save('maps/map_heatmap.html')
    #with open('map.html') as f:
    #    map_html = f.read()
    #print(map_html)
    map_html = m.get_root().render()

    dash_app.layout = html.Div([

        html.Div([
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
                    <div class="navbar navbar-static-top" >
                    <div class="navbar-inner" style="background-image: none !important; background-color: rgb(29, 161, 242); !important; border: none !important">
                        <div class="container">
                            <a href="/home/" class="brand" style="text-shadow: none;">Twitter Happiness</a>
                            <ul class="nav">
                                <li><a href="/tweets-list/" style="text-shadow: none;">Tweets List</a></li>
                                <li><a href="/tweets-map/" style="text-shadow: none;">Tweets Map</a></li>                            
                            </ul>
                            <ul class="nav pull-right">
                                <li><a href="/about-us/" style="text-shadow: none;">About Us</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
                ''')
        ]),

        html.Div([

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                dcc.RangeSlider(
                    id='date-slider',
                    min=-5,
                    max=0,
                    value=[-5, 0]
                )], style={'width': '80%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Iframe(id='map', srcDoc=map_html, width='100%', height='600'), # open('map.html', 'r').read()

            #dash_dangerously_set_inner_html.DangerouslySetInnerHTML(map_html)
        ],
            style={'width': '80%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()


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
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
                <div class="navbar navbar-static-top" >
                <div class="navbar-inner" style="background-image: none !important; background-color: rgb(29, 161, 242); !important; border: none !important">
                    <div class="container">
                        <a href="/home/" class="brand" style="text-shadow: none;">Twitter Happiness</a>
                        <ul class="nav">
                            <li><a href="/tweets-list/" style="text-shadow: none;">Tweets List</a></li>
                            <li><a href="/tweets-map/" style="text-shadow: none;">Tweets Map</a></li>                            
                        </ul>
                        <ul class="nav pull-right">
                            <li><a href="/about-us/" style="text-shadow: none;">About Us</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            ''')
        ]),

        html.Div([

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                dcc.Dropdown(
                    id='locations-filter',
                    options=[{'label': loc["name"], 'value': loc["name"]} for loc in locations],
                    value=location
                )], style={'width': '50%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

            html.Div([
                dcc.RangeSlider(
                    id='date-slider',
                    min=-days_history,
                    max=0,
                    marks=days_markers,
                    value=[-days_history, 0]
                )], style={'width': '80%', 'margin': 'auto'}),

            html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

            html.Div([
                html.Div(dcc.Graph(id='tweets-map'), style={'width': '75%', 'display': 'inline-block'}),
                html.Div(style={'width': '10%', 'display': 'inline-block'}),
                html.Div(
                    id='tweets-list', style={'width': '15%', 'display': 'inline-block', 'vertical-align': 'top',
                                             'padding-top': '105px', 'line-height': '200%', 'position': 'static',
                                             'overflow': 'auto', 'white-space': 'pre-line'})
            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '150px'}),

            html.Div(id='selected-tweet')
        ],
            style={'width': '80%', 'margin': 'auto'}
        )

    ])

    return dash_app.index()


@dash_app.callback(
    dash.dependencies.Output('tweets-list', 'children'),
    [
        dash.dependencies.Input('locations-filter', 'value')
    ]
)
def update_tweets_list(location_filter):
    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    # print(location)

    location_query = {
        "lat": {
            "$gt": location["lat_min"],
            "$lt": location["lat_max"]
        },
        "lon": {
            "$gt": location["lon_min"],
            "$lt": location["lon_max"]
        }
    }
    tweets = MONGO.db[DB_TWEETS].find(location_query)[:2]

    html_content = '<div class="tweets-scrolling-box" > '
    for tweet in tweets:
        # {white-space: pre-line;}
        html_content += '<div>' + tweet['text'] + '</div>'
    html_content = ''.join([html_content, '</div>'])

    content = html.Div(
        dash_dangerously_set_inner_html.DangerouslySetInnerHTML(html_content))
    return content


@dash_app.callback(
    dash.dependencies.Output('tweets-map', 'figure'),
    [
        dash.dependencies.Input('locations-filter', 'value'),
        dash.dependencies.Input('date-slider', 'value')
    ]
)
def update_tweets_map(location_filter, date_filter):

    mapbox_access_token = 'pk.eyJ1IjoiZWR1cmYiLCJhIjoiY2pvOTg2NWFjMDd0MjN2b2pveXcxam1taCJ9.1vQR8y_zH5YsUkbJbdOjaw'

    min_day = datetime.datetime.today().replace(hour=00, minute=00) + datetime.timedelta(days=date_filter[0])
    max_day = datetime.datetime.today().replace(hour=23, minute=59) + datetime.timedelta(days=date_filter[1])
    print(min_day, ' - ', max_day)

    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    #print(location)

    location_query = {
        "lat": {
            "$gt": location["lat_min"],
            "$lt": location["lat_max"]
        },
        "lon": {
            "$gt": location["lon_min"],
            "$lt": location["lon_max"]
        }
    }
    tweets = MONGO.db[DB_TWEETS].find(location_query) #[:300]

    sentiment_class_colors = {
        -2: "rgb(255, 0, 0)",
        -1: "rgb(255, 102, 0)",
        0: "rgb(255, 255, 0)",
        1: "rgb(153, 255, 51)",
        2: "rgb(0, 255, 0)",
    }

    lats = []
    lons = []
    texts = []
    colors = []
    for tweet in tweets:
        lats.append(tweet["lat"])
        lons.append(tweet["lon"])
        texts.append("<br>".join(textwrap.wrap(tweet["text"],50)))
        sentiment_class = tweet["class"]
        colors.append(sentiment_class_colors[sentiment_class])

    #print(len(lats), "tweets loaded")

    data = [
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(
                # symbol="square",
                size=14,
                color=colors,
            ),
            text=texts,
            hoverinfo='text'  # 'name + x + y + text'
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

    map1 = dict(data=data, layout=layout)

    return map1


@dash_app.callback(
    dash.dependencies.Output('selected-tweet', 'children'),
    [
        dash.dependencies.Input('tweets-map', 'hoverData')
    ]
)
def display_data(hover_point):
    #print(hover_point)
    return json.dumps(hover_point, indent=2)


if __name__ == '__main__':
    flask_app.run()
    # dash_app.run_server()
