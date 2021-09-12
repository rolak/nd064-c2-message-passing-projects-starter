#!/bin/bash

docker image tag rest-controller:latest rolak/rest-controller:latest
docker image push rolak/rest-controller:latest
