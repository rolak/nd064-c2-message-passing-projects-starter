import json
import os
from datetime import datetime
from typing import Optional, List

import grpc
import helpers.controller_pb2 as controller__pb2
import helpers.controller_pb2_grpc as controller__pb2_grpc
from flask import request, Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from helpers.models import Connection, Location, Person
from helpers.schemas import (
    ConnectionSchema,
    LocationSchema,
    PersonSchema,
)
from kafka import KafkaProducer

GRPC_LOCATION_TARGET = os.getenv("GRPC_LOCATION_TARGET") or "localhost:5061"
GRPC_PERSON_TARGET = os.getenv("GRPC_PERSON_TARGET") or "localhost:5062"
GRPC_CONNECTIONS_TARGET = os.getenv("GRPC_CONNECTIONS_TARGET") or "localhost:5063"
TOPIC_NAME = os.getenv("TOPIC_NAME") or 'locations'
KAFKA_SERVER = os.getenv("KAFKA_SERVER") or 'localhost:9092'

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via geolocation.")  # noqa


# TODO: This needs better exception handling


@api.route("/locations")
@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @accepts(schema=LocationSchema)
    def post(self):
        producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)
        print(request.get_json())
        kafka_data = json.dumps(request.get_json()).encode()
        producer.send(TOPIC_NAME, kafka_data)
        # producer.flush()
        return Response(status=202)

    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        channel = grpc.insecure_channel(GRPC_LOCATION_TARGET)
        stub = controller__pb2_grpc.LocationServiceStub(channel)
        id_message = controller__pb2.IdRequest(
            id=int(location_id)
        )
        response = stub.Get(id_message)

        location_response = {
            "id": response.id,
            "person_id": response.person_id,
            "longitude": response.longitude,
            "latitude": response.latitude,
            "creation_time": datetime.strptime(response.creation_time, '%Y-%m-%d %H:%M:%S')
        }
        return location_response


@api.route("/persons")
class PersonsResource(Resource):
    @accepts(schema=PersonSchema)
    @responds(schema=PersonSchema)
    def post(self) -> Person:
        payload = request.get_json()
        channel = grpc.insecure_channel(GRPC_PERSON_TARGET)
        stub = controller__pb2_grpc.PersonsServiceStub(channel)
        person_request = controller__pb2.PersonMessage(
            id=0,
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            company_name=payload["company_name"]
        )
        response = stub.Create(person_request)
        return response

    @responds(schema=PersonSchema, many=True)
    def get(self) -> List[Person]:
        channel = grpc.insecure_channel(GRPC_PERSON_TARGET)
        stub = controller__pb2_grpc.PersonsServiceStub(channel)
        response = stub.GetList(controller__pb2.Empty())
        return response.persons


@api.route("/persons/<person_id>")
@api.param("person_id", "Unique ID for a given Person", _in="query")
class PersonResource(Resource):
    @responds(schema=PersonSchema)
    def get(self, person_id) -> Person:
        channel = grpc.insecure_channel(GRPC_PERSON_TARGET)
        stub = controller__pb2_grpc.PersonsServiceStub(channel)
        person_request = controller__pb2.IdRequest(
            id=int(person_id)
        )
        response = stub.Get(person_request)
        return response


@api.route("/persons/<person_id>/connection")
@api.param("start_date", "Lower bound of date range", _in="query")
@api.param("end_date", "Upper bound of date range", _in="query")
@api.param("distance", "Proximity to a given user in meters", _in="query")
class ConnectionDataResource(Resource):
    @responds(schema=ConnectionSchema, many=True)
    def get(self, person_id) -> ConnectionSchema:
        start_date: datetime = datetime.strptime(
            request.args["start_date"], DATE_FORMAT
        )
        end_date: datetime = datetime.strptime(request.args["end_date"], DATE_FORMAT)
        distance: Optional[int] = request.args.get("distance", 5)

        channel = grpc.insecure_channel(GRPC_CONNECTIONS_TARGET)
        stub = controller__pb2_grpc.ConnectionsServiceStub(channel)
        connection_request = controller__pb2.ConnectionRequest(
            person_id=int(person_id),
            start_date=str(start_date),
            end_date=str(end_date),
            meters=int(distance)
        )
        response = stub.Get(connection_request)

        response_list = []
        for res in response.connections:
            location_response = {
                "id": res.location.id,
                "person_id": res.location.person_id,
                "longitude": res.location.longitude,
                "latitude": res.location.latitude,
                "creation_time": datetime.strptime(res.location.creation_time, '%Y-%m-%d %H:%M:%S')
            }
            response_list.append(
                Connection(
                    person=res.person, location=location_response,
                )
            )
        return response_list
