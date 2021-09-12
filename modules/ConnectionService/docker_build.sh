#!/bin/bash

cd .. && docker build -t connection-service -f ConnectionService/Dockerfile .
