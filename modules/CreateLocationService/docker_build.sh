#!/bin/bash

cd .. && docker build -t create-location-service  -f CreateLocationService/Dockerfile .
