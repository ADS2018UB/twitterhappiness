from flask import Flask
from flask import render_template
from flask import Flask, make_response, request
from flask_pymongo import PyMongo

from flask import abort, jsonify, redirect, render_template
from flask import request, url_for
from forms import ProductForm

import json
from bson.objectid import ObjectId
import bson

from flask_login import LoginManager, current_user
from flask_login import login_user, logout_user

from forms import LoginForm
from models import User

from flask_login import login_required

import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_dangerously_set_inner_html
import plotly.graph_objs as go
import pandas as pd

from data import load_data

# dash_app = dash.Dash(__name__)
# flask_app = dash_app.server

flask_app = Flask(__name__)
dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname='/dashboards')
dash_app.config.suppress_callback_exceptions = True
dash_app.layout = html.Div()
dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/bootswatch/2.3.2/united/bootstrap.min.css"})
dash_app.css.append_css(
    {'external_url': "https://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-responsive.min.css"})

mlab_credentials_file = "../credentials/mlab_credentials.txt"
DB_TWEETS = "twitter_happiness_test"
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


@flask_app.route('/tweets-map/')
def tweets_map():
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
                            <li><a href="/about-us/" style="text-shadow: none;">About Us</a></li>
                        </ul>
                        <ul class="nav pull-right">
                            <li><a href="{{ url_for('login') }}" style="text-shadow: none;">Login</a></li>
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
                html.Div(dcc.Graph(id='tweets-map'), style={'width': '75%', 'display': 'inline-block'}),
                html.Div(style={'width': '10%', 'display': 'inline-block'}),
                html.Div(
                    id='tweets-list', style={'width': '15%', 'display': 'inline-block', 'vertical-align': 'top',
                                             'padding-top': '105px', 'line-height': '200%', 'position': 'static',
                                             'overflow': 'auto', 'white-space': 'pre-line'})
            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '150px'}),
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
        dash.dependencies.Input('locations-filter', 'value')
    ]
)
def update_tweets_map(location_filter):
    mapbox_access_token = 'pk.eyJ1IjoiZWR1cmYiLCJhIjoiY2pvOTg2NWFjMDd0MjN2b2pveXcxam1taCJ9.1vQR8y_zH5YsUkbJbdOjaw'

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
    tweets = MONGO.db[DB_TWEETS].find(location_query)[:300]

    sent_class_color = {
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
        texts.append(tweet["text"])
        sent_class = tweet["class"]
        colors.append(sent_class_color[sent_class])

    print(len(lats), "tweets loaded")

    data = [
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(
                #symbol="square",
                size=14,
                color=colors,
            ),
            text=texts,
            hoverinfo='text'
        )
    ]

    layout = go.Layout(
        autosize=True,
        height=800,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=(location["lat_min"] + location["lat_max"]) / 2,
                lon=(location["lon_min"] + location["lon_max"]) / 2
            ),
            pitch=0,
            zoom=10
        ),
    )

    map1 = dict(data=data, layout=layout)

    '''layout = dict(
        autosize=True,
        
        font=dict(color='#CCCCCC'),
        titlefont=dict(color='#CCCCCC', size='14'),
        margin=dict(
            l=35,
            r=35,
            b=35,
            t=45
        ),
        hovermode="closest",
        plot_bgcolor="#191A1A",
        paper_bgcolor="#020202",
        legend=dict(font=dict(size=10), orientation='h'),
        title='Satellite Overview',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style="dark",
            center=dict(
                lon=41.408366,
                lat=2.137533,
                zoom = 7
            )
        )
    )
    trace = dict(
        type='scattermapbox',
        lon=[41.408366, 41.407288],
        lat=[2.137533, 2.138364],
        text='Well_Name',
        name='well_type',
        marker=dict(
            size=4,
            opacity=0.8,
            color='blue'
        )
    )
    map1 = dict(data=trace, layout=layout)'''

    return map1


if __name__ == '__main__':
    flask_app.run()
    # dash_app.run_server()
