
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
import about_us_details

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
    return render_template('about_us/about_us.html', details=about_us_details.DETAILS)


# DASHBOARD COMPONENTS

DASHBOARD_HEADER_HTML = '''
    <div class="navbar navbar-static-top" >
        <div class="navbar-inner">
            <div class="container">
                <a href="/home/" class="brand nav-link" style="text-shadow: none;">Twitter Happiness</a>
                <ul class="nav">
                    <li><a href="/tweets-list/" class="nav-link" style="text-shadow: none;">Tweets List</a></li>
                    <li><a href="/tweets-map/" class="nav-link" style="text-shadow: none;">Tweets Map</a></li>
                    <li><a href="/tweets-tl/" class="nav-link" style="text-shadow: none;">Tweets TL</a></li>
                </ul>
                <ul class="nav pull-right">
                    <li><a href="/about-us/" class="nav-link" style="text-shadow: none;">About Us</a></li>
                </ul>
            </div>
        </div>
    </div>
'''


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
        dash.dependencies.Input('locations-filter', 'value'),
        dash.dependencies.Input('date-slider', 'value')
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

                    html.Div([
                        dcc.Dropdown(
                            id='locations-filter',
                            options=[{'label': loc["name"], 'value': loc["name"]} for loc in locations],
                            value=location
                        ),
                        ], style={'width': '50%', 'display': 'inline-block'}
                    ),  # 'margin': 'auto'}),

                    html.Div([
                        dcc.RadioItems(
                            id='map-type',
                            options=[{'label': ' '+i, 'value': i} for i in ['Circles', 'Icons', 'Heatmap']],
                            value='Circles',
                            labelStyle={'display': 'inline-block', 'margin-left': '10px', 'margin-right': '10px', 'word-spacing': '5px'}
                        )
                        ], style={'margin-left': '10%', 'display': 'inline-block', 'vertical-align': 'top'}

                    )
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
        dash.dependencies.Input('date-slider', 'value'),
    ]
)
def update_tweets_list(location_filter, date_filter):

    min_day = datetime.datetime.today().replace(hour=00, minute=00, second=00) + datetime.timedelta(days=date_filter[0])
    max_day = datetime.datetime.today().replace(hour=23, minute=59, second=59) + datetime.timedelta(days=date_filter[1])
    #print(min_day, ' - ', max_day)

    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    #print(location)

    location_query = {
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
    tweets = MONGO.db[DB_TWEETS].find(location_query)  # [:300]

    #tweets_list = [tweet for tweet in tweets]
    #html_content = '<div class="tweets-scrolling-box" > '
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
        dash.dependencies.Input('date-slider', 'value')
    ]
)
def update_tweets_map(location_filter, map_type, date_filter):
    root_url = request.url_root

    mapbox_access_token = 'pk.eyJ1IjoiZWR1cmYiLCJhIjoiY2pvOTg2NWFjMDd0MjN2b2pveXcxam1taCJ9.1vQR8y_zH5YsUkbJbdOjaw'

    min_day = datetime.datetime.today().replace(hour=00, minute=00, second=00) + datetime.timedelta(days=date_filter[0])
    max_day = datetime.datetime.today().replace(hour=23, minute=59, second=59) + datetime.timedelta(days=date_filter[1])
    #print(min_day, ' - ', max_day)

    location = MONGO.db[DB_LOCATIONS].find({"name": location_filter})[0]
    #print(location)

    location_query = {
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
    tweets = MONGO.db[DB_TWEETS].find(location_query)

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
