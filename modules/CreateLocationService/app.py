import json
import logging
import os
from multiprocessing import Process
from typing import Dict

from geoalchemy2.functions import ST_Point
from kafka import KafkaConsumer

from helpers import create_app  # noqa
from helpers import db  # noqa
from helpers.models import Location
# from helpers.schemas import LocationSchema
from helpers.schemas import LocationSchema

FLASK_PORT = os.getenv("FLASK_PORT") or "5050"
FLASK_HOST = os.getenv("FLASK_HOST") or "0.0.0.0"
FLASK_DEBUG = os.getenv("FLASK_DEBUG") or "True"
TOPIC_NAME = os.getenv("TOPIC_NAME") or "locations"
KAFKA_SERVER = os.getenv("KAFKA_SERVER") or 'localhost:9092'

app = create_app(os.getenv("FLASK_ENV") or "test")

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


def run():
    with app.app_context():
        consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers=KAFKA_SERVER)
        for message in consumer:
            message_decode = json.loads(message.value.decode('UTF-8'))
            logger.info(f"Obtain message: {message_decode}")
            validation_results: Dict = LocationSchema().validate(message_decode)
            if validation_results:
                logger.warning(f"Unexpected data format in payload: {validation_results}")
            else:
                new_location = Location()
                new_location.person_id = message_decode["person_id"]
                new_location.creation_time = message_decode["creation_time"]
                new_location.coordinate = ST_Point(message_decode["latitude"], message_decode["longitude"])
                db.session.add(new_location)
                db.session.commit()


def run_flask():
    app.run(debug=FLASK_DEBUG, use_reloader=False, host=FLASK_HOST, port=FLASK_PORT)


if __name__ == "__main__":
    app.app_context().push()
    Process(target=run_flask).start()
    Process(target=run).start()
