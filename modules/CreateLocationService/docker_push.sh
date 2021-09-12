#!/bin/bash

docker image tag create-location-service:latest rolak/create-location-service:latest
docker image push rolak/create-location-service:latest
