#!/bin/bash

docker image tag location-service:latest rolak/location-service:latest
docker image push rolak/location-service:latest
