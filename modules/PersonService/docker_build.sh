#!/bin/bash

cd .. && docker build -t person-service -f PersonService/Dockerfile .
