from helpers.config import config_by_name  # noqa

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(env=None):
    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])

    db.init_app(app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app

