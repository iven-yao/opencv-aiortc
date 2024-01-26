FROM ubuntu:22.04

RUN apt-get update -y
RUN apt install libgl1-mesa-glx -y
RUN apt-get install 'ffmpeg' 'libsm6' 'libxext6' -y
RUN apt-get install python3-pip -y

RUN pip install aiortc
RUN pip install numpy
RUN pip install opencv-python

ADD server.py /server/

EXPOSE 1234

WORKDIR /server/
