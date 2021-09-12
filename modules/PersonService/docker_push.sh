#!/bin/bash

docker image tag person-service:latest rolak/person-service:latest
docker image push rolak/person-service:latest
