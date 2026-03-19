#!/bin/bash
sudo docker stop sixsense-final-test 2>/dev/null
sudo docker rm sixsense-final-test 2>/dev/null
sudo docker build -t doc-converter:latest .
sudo docker run -d -p 8000:8000 --name sixsense-final-test doc-converter:latest
sudo docker logs -f sixsense-final-test
