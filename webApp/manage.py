from flask_script import Manager
from app import flask_app

manager = Manager(flask_app)
flask_app.config['DEBUG'] = True # Ensure debugger will load.

if __name__ == '__main__':
    manager.run()