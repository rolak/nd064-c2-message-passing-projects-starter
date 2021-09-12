#!/bin/bash

docker image tag connection-service:latest rolak/connection-service:latest
docker image push rolak/connection-service:latest
