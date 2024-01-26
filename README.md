# Bouncing Ball
This project includes a server and client, which connect to each other through tcp socket with aiortc. Server generate a continuous image of a ball bouncing across the screen and send to client through tcp, client display received images with opencv and send the coordinates of the ball back to server. Then, server will compute the error of recieved coordinate and actual coordinates after recieving messages from client.

## Dependencies
- aiortc
- opencv-python
- numpy

## Usage
run server:
```
python3 server/server.py
```
run client:
```
python3 client/client.py
```
run tests:
```
pytest
```
build docker images:
```
docker compose build
```

## known issue
- PyAV and OpenCV conflict on Ubuntu 22.04, downgrade PyAV to 8.1.0 could temp solve this problem [#1](https://github.com/PyAV-Org/PyAV/issues/751) [#2](https://github.com/aiortc/aiortc/discussions/734)
