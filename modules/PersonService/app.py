import logging
import os
from concurrent import futures
from multiprocessing import Process

import grpc

from helpers import controller_pb2
from helpers import controller_pb2_grpc
from helpers import create_app  # noqa
from helpers import db  # noqa
from helpers.models import Person

FLASK_PORT = os.getenv("FLASK_PORT") or "5052"
FLASK_HOST = os.getenv("FLASK_HOST") or "0.0.0.0"
FLASK_DEBUG = os.getenv("FLASK_DEBUG") or "True"
GRPC_PERSON_SERVICE = os.getenv("GRPC_PERSON_SERVICE") or "[::]:5062"

app = create_app(os.getenv("FLASK_ENV") or "test")

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class PersonService(controller_pb2_grpc.PersonsServiceServicer):

    def Create(self, request, context):
        with app.app_context():
            new_person = Person()
            new_person.first_name = request.first_name
            new_person.last_name = request.last_name
            new_person.company_name = request.company_name
            db.session.add(new_person)
            db.session.commit()
            person_result = controller_pb2.PersonMessage(
                id=int(new_person.id),
                first_name=new_person.first_name,
                last_name=new_person.last_name,
                company_name=new_person.company_name
            )
            return person_result

    def Get(self, request, context):
        with app.app_context():
            person = db.session.query(Person).get(request.id)
            person_result = controller_pb2.PersonMessage(
                id=int(person.id),
                first_name=person.first_name,
                last_name=person.last_name,
                company_name=person.company_name
            )
            return person_result

    def GetList(self, request, context):
        with app.app_context():
            person_list = db.session.query(Person).all()
        result = controller_pb2.PersonsMessageList()
        for person in person_list:
            person_result = controller_pb2.PersonMessage(
                id=int(person.id),
                first_name=person.first_name,
                last_name=person.last_name,
                company_name=person.company_name
            )
            result.persons.extend([person_result])
        return result


def run():
    with app.app_context():
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        controller_pb2_grpc.add_PersonsServiceServicer_to_server(PersonService(), server)
        server.add_insecure_port(GRPC_PERSON_SERVICE)
        server.start()
        server.wait_for_termination()


def run_flask():
    app.run(debug=FLASK_DEBUG, use_reloader=False, host=FLASK_HOST, port=FLASK_PORT)


if __name__ == "__main__":
    app.app_context().push()
    Process(target=run_flask).start()
    Process(target=run).start()
