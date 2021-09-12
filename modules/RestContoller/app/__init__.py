from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api

from helpers.models import Connection, Location, Person  # noqa
from helpers.schemas import ConnectionSchema, LocationSchema, PersonSchema  # noqa


def create_app(env=None):
    app = Flask(__name__)
    api = Api(app, title="UdaConnect API", version="0.1.0")

    CORS(app)  # Set CORS for development

    register_routes(api, app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app


def register_routes(api, app, root="api"):
    from app.controllers import api as udaconnect_api

    api.add_namespace(udaconnect_api, path=f"/{root}")
