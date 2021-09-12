#!/bin/bash

cd .. && docker build -t location-service -f LocationService/Dockerfile .
