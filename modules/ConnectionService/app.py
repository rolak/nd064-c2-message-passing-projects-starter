import logging
import os
from concurrent import futures
from datetime import datetime, timedelta
from multiprocessing import Process
from typing import Dict, List

import grpc
from sqlalchemy.sql import text

from helpers import controller_pb2
from helpers import controller_pb2_grpc
from helpers import create_app  # noqa
from helpers import db  # noqa
from helpers.models import Connection, Location, Person



DATA_FORMAT = "%Y-%m-%d %H:%M:%S"

FLASK_PORT = os.getenv("FLASK_PORT") or "5053"
FLASK_HOST = os.getenv("FLASK_HOST") or "0.0.0.0"
FLASK_DEBUG = os.getenv("FLASK_DEBUG") or "True"
GRPC_PERSON_TARGET = os.getenv("GRPC_PERSON_TARGET") or "localhost:5062"
GRPC_CONNECTION_SERVICE = os.getenv("GRPC_CONNECTION_SERVICE") or "[::]:5063"

app = create_app(os.getenv("FLASK_ENV") or "test")

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class ConnectionsService(controller_pb2_grpc.ConnectionsServiceServicer):
    def Get(self, request, context):

        # def find_contacts(person_id: int, start_date: datetime, end_date: datetime, meters=5
        #                   ) -> List[Connection]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?
        """
        with app.app_context():
            print(request.start_date)
            print(request.end_date)
            person_id = request.person_id
            start_date = datetime.strptime(request.start_date, DATA_FORMAT)
            end_date = datetime.strptime(request.end_date, DATA_FORMAT)
            meters = request.meters

            locations: List = db.session.query(Location).filter(
                Location.person_id == person_id
            ).filter(Location.creation_time < end_date).filter(
                Location.creation_time >= start_date
            ).all()

            channel = grpc.insecure_channel(GRPC_PERSON_TARGET)
            stub = controller_pb2_grpc.PersonsServiceStub(channel)
            response = stub.GetList(controller_pb2.Empty())

            # Cache all users in memory for quick lookup
            person_map: Dict[str, Person] = {person.id: person for person in response.persons}

            # Prepare arguments for queries
            data = []
            for location in locations:
                data.append(
                    {
                        "person_id": person_id,
                        "longitude": location.longitude,
                        "latitude": location.latitude,
                        "meters": meters,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    }
                )

            query = text(
                """
            SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
            FROM    location
            WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
            AND     person_id != :person_id
            AND     TO_DATE(:start_date, 'YYYY-MM-DD') <= creation_time
            AND     TO_DATE(:end_date, 'YYYY-MM-DD') > creation_time;
            """
            )
            result: List[Connection] = []
            for line in tuple(data):
                for (
                        exposed_person_id,
                        location_id,
                        exposed_lat,
                        exposed_long,
                        exposed_time,
                ) in db.engine.execute(query, **line):
                    location = Location(
                        id=location_id,
                        person_id=exposed_person_id,
                        creation_time=exposed_time,
                    )
                    location.set_wkt_with_coords(exposed_lat, exposed_long)

                    result.append(
                        Connection(
                            person=person_map[exposed_person_id], location=location,
                        )
                    )

            grpc_results = controller_pb2.ConnectionsMessageList()
            for connection in result:
                person_result = controller_pb2.PersonMessage(
                    id=int(connection.person.id),
                    first_name=connection.person.first_name,
                    last_name=connection.person.last_name,
                    company_name=connection.person.company_name
                )
                location_result = controller_pb2.LocationMessage(
                    id=int(connection.location.id),
                    person_id=int(connection.location.person_id),
                    longitude=str(connection.location.longitude),
                    latitude=str(connection.location.latitude),
                    creation_time=str(connection.location.creation_time),
                )

                connection_result = controller_pb2.ConnectionMessage(
                    person=person_result,
                    location=location_result
                )
                grpc_results.connections.extend([connection_result])
            return grpc_results


def run():
    with app.app_context():
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        controller_pb2_grpc.add_ConnectionsServiceServicer_to_server(ConnectionsService(), server)
        server.add_insecure_port(GRPC_CONNECTION_SERVICE)
        server.start()
        server.wait_for_termination()


def run_flask():
    app.run(debug=FLASK_DEBUG, use_reloader=False, host=FLASK_HOST, port=FLASK_PORT)


if __name__ == "__main__":
    app.app_context().push()
    Process(target=run_flask).start()
    Process(target=run).start()
