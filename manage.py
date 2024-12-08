from flask import Flask
from flask_migrate import Migrate
from community_cyber_alert import app, db

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()
