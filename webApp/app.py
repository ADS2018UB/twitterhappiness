
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

#dash_app = dash.Dash(__name__)
#flask_app = dash_app.server

flask_app = Flask(__name__)
dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname='/dashboards')
dash_app.config.suppress_callback_exceptions = True
dash_app.layout = html.Div()
dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/bootswatch/2.3.2/united/bootstrap.min.css"})
dash_app.css.append_css({'external_url': "https://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-responsive.min.css"})



mlab_credentials_file = "../credentials/mlab_credentials.txt"
DB_TWEETS = "twitter_happiness_test"
DB_LOCATIONS = "twitter_happiness_locations"
DB_UP = False
PROD_ENV = True
PROD_ENV = False


def db_connect():
    global DB_UP
    global PROD_ENV
    global MONGO
    global flask_app

    if PROD_ENV:
        print("PROD environment")
        name = os.environ["fooApp_DB_USERNAME"]
        password = os.environ["fooApp_DB_PASS"]
        url = os.environ["fooApp_DB_URL"]
        dbname = os.environ["fooApp_DB_NAME"]
    else:
        print("DEV environment")
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

flask_app.config['SECRET_KEY'] = 'enydM2ANhdcoKwdVa0jWvEsbPFuQpMjf' # Create your own.
flask_app.config['SESSION_PROTECTION'] = 'strong'


# Use Flask-Login to track current user in Flask's session.
login_manager = LoginManager()
login_manager.setup_app(flask_app)
login_manager.login_view = 'login'

filtered_location = None


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login hook to load a User instance from ID."""
    u = MONGO.db.users.find_one({"username": user_id})
    if not u:
        return None
    return User(u['username'])


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


"""
@flask_app.route('/db/', methods=['GET', 'POST'])
def db_credentials():
    #Provide HTML form to edit DB credentials.
    form = DBCredentialsForm(request.form)
    if request.method == 'POST' and form.validate():
        with open(mlab_credentials_file, 'w', encoding='utf-8') as f:
            f.write(form.data["credentials"])
            print(form.data["credentials"])
        db_connect()
        return render_template('credentials/db_credentials_updated.html', db_status = str(DB_UP))
    # Either first load or validation error at this point.
    return render_template('credentials/db_credentials.html', form=form)
"""


@flask_app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('products_list'))
    form = LoginForm(request.form)
    error = None
    if request.method == 'POST' and form.validate():
        username = form.username.data.lower().strip()
        password = form.password.data.lower().strip()
        user = MONGO.db.users.find_one({"username": form.username.data})
        print(username)
        # print(username, password)
        if user and User.validate_login(form.password.data, user['password']):
            user_obj = User(user['username'])
            login_user(user_obj)
            return redirect(url_for('products_list'))
        else:
            error = 'Incorrect username or password.'
    return render_template('user/login.html',form=form, error=error)


@flask_app.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('products_list'))


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


@flask_app.route('/tweets-map-old/')
def tweets_map_old():
    """Provide HTML listing of all Tweets."""
    tweets = MONGO.db[DB_TWEETS].find()[30:50]
    return render_template('tweets/list.html', tweets=tweets)


@flask_app.route('/about-us/')
def about_us():
    """Provide HTML listing of all Tweets."""
    tweets = MONGO.db[DB_TWEETS].find()[50:60]
    return render_template('tweets/list.html', tweets=tweets)


@flask_app.route('/products/')
def products_list():
    # return 'Listing of all products we have.'
    """Provide HTML listing of all Products."""
    # Query: Get all Products objects, sorted by date.
    products = MONGO.db.products.find()[:]
    return render_template('product/index.html', products=products)


@flask_app.route('/products/create/', methods=['GET', 'POST'])
@login_required
def product_create():
    # return 'Form to create a new product.'
    """Provide HTML form to create a new product."""
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        MONGO.db.products.insert_one(form.data)
        # Success. Send user back to full product list.
        return redirect(url_for('products_list'))
    # Either first load or validation error at this point.
    return render_template('product/create.html', form=form)


@flask_app.route('/products/<product_id>/')
def product_detail(product_id):
    # return 'Detail of product     #{}.'.format(product_id)
    """Provide HTML page with a given product."""
    # Query: get Product object by ID.
    product = MONGO.db.products.find_one({"_id": ObjectId(product_id) })
    print(product)
    if product is None:
        # Abort with Not Found.
        abort(404)
    return render_template('product/detail.html', product=product) # this is the controler, linking view (template) and model (data, product)


@flask_app.route('/products/<product_id>/edit/', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    # return 'Form to edit product #.'.format(product_id)
    """Provide HTML form to edit an existing product."""
    product = MONGO.db.products.find_one({"_id": ObjectId(product_id)})
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():
        MONGO.db.products.replace_one({'_id':ObjectId(product_id)},form.data)
        # Success. Send user back to full product list.
        return redirect(url_for('products_list'))
    # Either first load or validation error at this point.
    return render_template('product/edit.html', form=form, product=product)


@flask_app.route('/products/<product_id>/delete/', methods=['DELETE'])
@login_required
def product_delete(product_id):
    # raise NotImplementedError('DELETE')
    """Delete record using HTTP DELETE, respond with JSON."""
    result = MONGO.db.products.delete_one({ "_id": ObjectId(product_id) })
    if result.deleted_count == 0:
        # Abort with Not Found, but with simple JSON response.
        response = jsonify({'status': 'Not Found'})
        response.status = 404
        return response
    return jsonify({'status': 'OK'})


@flask_app.route('/string/')
def return_string():
    dump = dump_request_detail(request)
    return 'Hello, world!'


@flask_app.route('/object/')
def return_object():
    dump = dump_request_detail(request)
    headers = {'Content-Type': 'text/plain'}
    return make_response(Response('Hello, world! \n' + dump, status=200, headers=headers))


@flask_app.route('/tuple/<path:resource>')
def return_tuple(resource):
    dump = dump_request_detail(request)
    return 'Hello, world! \n' + dump, 200, {'Content-Type':'text/plain'}


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
            '''),
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

            dcc.Graph(id='tweets-map'),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '150px'}),



        ],
        style={'width': '80%', 'margin': 'auto'}
        )
    ])

    return dash_app.index()


@dash_app.callback(
    dash.dependencies.Output('tweets-map', 'figure'),
    [
        dash.dependencies.Input('locations-filter', 'value')
    ]
)
def update_tweets_map(location_filter):

    mapbox_access_token = 'pk.eyJ1IjoiZWR1cmYiLCJhIjoiY2pvOTg2NWFjMDd0MjN2b2pveXcxam1taCJ9.1vQR8y_zH5YsUkbJbdOjaw'

    location = MONGO.db[DB_LOCATIONS].find({"name":location_filter})[0]
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
    tweets = MONGO.db[DB_TWEETS].find(location_query)[:100]

    lats = []
    lons = []
    texts = []
    colors = []
    for tweet in tweets:
        lats.append(tweet["lat"])
        lons.append(tweet["lon"])
        texts.append(tweet["text"])
        sentiment = tweet["sentiment"]
        colors.append("red" if sentiment==-1 else "yellow" if sentiment==0 else "green" if sentiment==1 else "black")

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
                lat=(location["lat_min"]+location["lat_max"])/2,
                lon=(location["lon_min"]+location["lon_max"])/2
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


data = load_data()


@flask_app.route('/dashboards/eurostat')
def dashboard_eurostat():
    global dash_app

    available_indicators = data['NA_ITEM'].sort_values(ascending=[True]).unique()
    countries_flg = data["Country"].sort_values(ascending=[True]).unique()
    years = data['TIME']

    dash_app.layout = html.Div([

        html.Div(style={'padding-top': '10px', 'padding-bottom': '10px'}),

        html.H1(children='Eurostat Dashboard', style={'margin': 'auto'}),

        html.Div(style={'padding-top': '10px', 'padding-bottom': '15px'}),

        html.Div([

            html.Div([

                html.Div([
                    dcc.Dropdown(
                        id='xaxis-column-1',
                        options=[{'label': i, 'value': i} for i in available_indicators],
                        value=available_indicators[0]
                    ),
                    html.Div(style={'padding-top': '5px', 'padding-bottom': '5px'}),
                    dcc.RadioItems(
                        id='xaxis-type-1',
                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),

                html.Div([
                    dcc.Dropdown(
                        id='yaxis-column-1',
                        options=[{'label': i, 'value': i} for i in available_indicators],
                        value=available_indicators[1]
                    ),
                    html.Div(style={'padding-top': '5px', 'padding-bottom': '5px'}),
                    dcc.RadioItems(
                        id='yaxis-type-1',
                        options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    )
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})

            ]),

            html.Div(style={'padding-top': '10px', 'padding-bottom': '20px'}),

            dcc.Slider(
                id='year-slider-1',
                min=years.min(),
                max=years.max(),
                value=years.max(),
                step=None,
                marks={str(year): str(year) for year in years.unique()}
            ),

            html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

            dcc.Graph(id='indicator-graphic-1')

        ]),

        html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

        html.Hr(),

        html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

        html.Div([

            html.Div([

                dcc.RadioItems(
                    id='countries-flg',
                    options=[{'label': i, 'value': i} for i in countries_flg],
                    value=countries_flg[0]
                ),

                html.Div([
                    dcc.Dropdown(
                        id='countries-2',
                        multi=True
                    ),
                ], style={'width': '48%', 'display': 'inline-block'}),

                html.Div([
                    dcc.Dropdown(
                        id='yaxis-column-2',
                        options=[{'label': i, 'value': i} for i in available_indicators],
                        value="Exports of goods"  # available_indicators[0]
                    ),
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})

            ]),

            html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'}),

            dcc.Graph(id='indicator-graphic-2')

        ]),

        html.Div(style={'padding-top': '20px', 'padding-bottom': '20px'})


    ],
        style={'width': '80%', 'margin': 'auto'}
    )

    return dash_app.index()


@dash_app.callback(
    dash.dependencies.Output('indicator-graphic-1', 'figure'),
    [
        dash.dependencies.Input('xaxis-column-1', 'value'),
        dash.dependencies.Input('yaxis-column-1', 'value'),
        dash.dependencies.Input('xaxis-type-1', 'value'),
        dash.dependencies.Input('yaxis-type-1', 'value'),
        dash.dependencies.Input('year-slider-1', 'value')
    ]
)
def update_graph_1(xaxis_column_name, yaxis_column_name, xaxis_type, yaxis_type, year_value):

    dff = data[data['TIME'] == year_value]

    graph1 = {
        'data': [go.Scatter(
            x=dff[dff['NA_ITEM'] == xaxis_column_name]['Value'],
            y=dff[dff['NA_ITEM'] == yaxis_column_name]['Value'],
            text=dff[dff['NA_ITEM'] == yaxis_column_name]['GEO'],
            mode='markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
            }
        )],
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
                'type': 'linear' if xaxis_type == 'Linear' else 'log'
            },
            yaxis={
                'title': yaxis_column_name,
                'type': 'linear' if yaxis_type == 'Linear' else 'log'
            },
            margin={'l': 60, 'b': 50, 't': 10, 'r': 0},
            hovermode='closest'
        )
    }

    return graph1


@dash_app.callback(
    dash.dependencies.Output('countries-2', 'options'),
    [dash.dependencies.Input('countries-flg', 'value')])
def set_countries_options(country_flg):
    available_countries = data[data["Country"] == country_flg]["GEO"].sort_values(ascending=[True]).unique()
    return [{'label': i, 'value': i} for i in available_countries]


@dash_app.callback(
    dash.dependencies.Output('countries-2', 'value'),
    [dash.dependencies.Input('countries-2', 'options')])
def set_countries_value(available_options):
    return [available_options[i]['value'] for i in range(0,1)]


@dash_app.callback(
    dash.dependencies.Output('indicator-graphic-2', 'figure'),
    [
        dash.dependencies.Input('countries-2', 'value'),
        dash.dependencies.Input('yaxis-column-2', 'value')
    ]
)
def update_graph_2(countries, yaxis_column_name):

    data_lines = []

    years = data['TIME']
    for country in countries:
        dff = data[(data['GEO'] == country) & (data['NA_ITEM'] == yaxis_column_name)]
        data_lines.append(
            go.Scatter(
                x=dff["TIME"],
                y=dff['Value'],
                text=country,
                mode='lines+markers',
                name=country,
                marker={
                    'size': 10,
                    'opacity': 0.8,
                    'line': {'width': 0.4}
                }
            )
        )

    graph2 = {
        'data': data_lines,
        'layout': go.Layout(
            xaxis={
                'title': 'YEAR',
                'tick0': years.min()-1,
                'dtick': 1,
                'range': [years.min()-1,years.max()+1]
            },
            yaxis={
                'title': yaxis_column_name
            },
            margin={'l': 60, 'b': 50, 't': 10, 'r': 0},
            hovermode='closest'
        )
    }

    return graph2


if __name__ == '__main__':
    flask_app.run()
    #dash_app.run_server()
