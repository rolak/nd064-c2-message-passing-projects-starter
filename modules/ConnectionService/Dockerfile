FROM python:3.7-alpine

RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev g++ python3-dev

# copy helpers files
COPY ./ConnectionService .
RUN rm helpers
COPY ./helpers helpers/
RUN pip3 install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
RUN pip3 install -r helpers/requirements.txt

EXPOSE 5053

CMD ["python", "app.py"]
