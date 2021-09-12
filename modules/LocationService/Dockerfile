FROM python:3.7-alpine

RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev g++ python3-dev

# copy helpers files
COPY ./LocationService .
RUN rm helpers
COPY ./helpers helpers/
RUN pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
RUN pip install -r helpers/requirements.txt

EXPOSE 5050

CMD ["python", "app.py"]

