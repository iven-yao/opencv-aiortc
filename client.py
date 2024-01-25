import argparse
import asyncio

import cv2

import numpy as np
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    MediaStreamTrack
)

from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling

from multiprocessing import Queue, Process, Value

class CustomVideoStreamTrack(MediaStreamTrack):
    """
    A Class of custom video stream track that recv frames from other track

    Attributes:
        track(VideoStreamTrack)
    """
    kind = "video"
    def __init__(self, track):
        """
        Initializing the custom stream track

        Parameters:
            track(VideoStreamTrack)
        """
        super().__init__()
        self.track = track

    async def recv(self):
        """
        Recieve frame from the track
        """
        frame = await self.track.recv()
        return frame

def find_center(img):
    """
    Return the center coordination of the white ball in a black background image

    Parameters:
        img(MatLike): a image with a white ball
    """
    mask = cv2.inRange(img, (100, 100, 100), (255, 255, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if(len(contours) > 0):
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

def BallTracking(img_q, x, y):
    """
    A Process keep finding center coordination of white ball if img queue is not empty

    Parameters:
        img_q(Queue): a queue of images
        x(Value): a int sharing state for x-coord
        y(Value): a int sharing state for y-coord
    """
    while img_q._notempty:
        img = img_q.get()
        x.value, y.value = find_center(img)
    
    
async def FrameTransport(pc, track, img_q, x, y):
    """
    Play video of the frames recieved from video stream track, while sending ball coords to channel

    Parameters:
        pc(RTCPeerConnection)
        track(VideoStreamTrack)
        img_q(Queue): a queue of images
        x(Value): a int sharing state for x-coord
        y(Value): a int sharing state for y-coord
    """
    videoStream = CustomVideoStreamTrack(track)
    channel = pc.createDataChannel('client')

    while True:
        try: 
            # get frame
            frame = await videoStream.recv()

            # show video
            img = frame.to_ndarray(format='bgr24')

            cv2.imshow("Bouncing Ball", img)
            cv2.waitKey(1)
            img_q.put(img)
            channel.send("[coords]:"+str(x.value)+","+str(y.value))

        except Exception:
            pass

async def run(pc, signaling):

    # create process_a
    img_q = Queue()
    coord_x = Value('i', 0)
    coord_y = Value('i', 0)
    process_a = Process(target=BallTracking, args=(img_q, coord_x, coord_y))

    @pc.on("track")
    async def on_track(track):
        try:
            process_a.start()
            await FrameTransport(pc, track, img_q, coord_x, coord_y)
        finally:
            process_a.join()
            cv2.destroyAllWindows()

    # connect signaling
    await signaling.connect()

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)

            if obj.type == "offer":
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bouncing Ball - client")
    add_signaling_arguments(parser)
    args = parser.parse_args(['-s','tcp-socket'])

    # create signaling and peer connection
    signaling = create_signaling(args)
    pc = RTCPeerConnection()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())