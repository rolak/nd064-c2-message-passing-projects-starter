## Run application 
`kubectl apply -f deployment/`

## For build and push images use 
`docker_build.sh`
`docker_push.sh`

## Generating gRPC files
`pip install grpcio-tools`

`python -m grpc_tools.protoc -I./ --python_out=./ --grpc_python_out=./ controller.proto`
