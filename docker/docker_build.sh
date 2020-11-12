#!/bin/bash

cd ..
docker build -f ./docker/Dockerfile . -t sharp_eye
cd docker
