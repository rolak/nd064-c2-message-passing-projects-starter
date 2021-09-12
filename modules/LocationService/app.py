import os
from concurrent import futures

import grpc
import logging
from multiprocessing import Process

from helpers.models import Location
from helpers import db  # noqa

from helpers import create_app  # noqa
from helpers import controller_pb2_grpc
from helpers import controller_pb2

FLASK_PORT = os.getenv("FLASK_PORT") or "5051"
FLASK_HOST = os.getenv("FLASK_HOST") or "0.0.0.0"
FLASK_DEBUG = os.getenv("FLASK_DEBUG") or "True"
GRPC_LOCATION_SERVICE = os.getenv("GRPC_LOCATION_SERVICE") or "[::]:5061"

app = create_app(os.getenv("FLASK_ENV") or "test")

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class LocationService(controller_pb2_grpc.LocationServiceServicer):
    def Get(self, request, context):
        request_value = {
            "id": request.id,
        }
        logger.debug(f"Message obtain: {request_value}")
        with app.app_context():
            location, coord_text = (
                db.session.query(Location, Location.coordinate.ST_AsText())
                    .filter(Location.id == request_value.get('id'))
                    .one()
            )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        location_response = {
            "id": location.id,
            "person_id": location.person_id,
            "longitude": location.longitude,
            "latitude": location.latitude,
            "creation_time": str(location.creation_time)
        }

        return controller_pb2.LocationMessage(**location_response)


def run():
    with app.app_context():
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        controller_pb2_grpc.add_LocationServiceServicer_to_server(LocationService(), server)
        server.add_insecure_port(GRPC_LOCATION_SERVICE)
        server.start()
        server.wait_for_termination()


def run_flask():
    app.run(debug=FLASK_DEBUG, use_reloader=False, host=FLASK_HOST, port=FLASK_PORT)


if __name__ == "__main__":
    app.app_context().push()
    Process(target=run_flask).start()
    Process(target=run).start()
