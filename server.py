import argparse
import asyncio
import math

import cv2
import numpy
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
from av import VideoFrame


class BouncingBall():
    def __init__(self):
        self.height = 240
        self.width = 320
        self.x = 11
        self.y = 11
        self.r = 10
        self.dx = 5
        self.dy = 5
        self.color = (0,0,255)

    def isCrossBound(self, coord, max):
        if coord-self.r <= 0 or coord+self.r >= max:
            return True
        
        return False
    
    def move(self):
        # black background
        img = numpy.zeros((self.height, self.width, 3), dtype='uint8')

        # check if crossing the bound and switching direction
        if self.isCrossBound(self.x, self.width):
            self.dx *= -1
        if self.isCrossBound(self.y, self.height):
            self.dy *= -1
        
        # move
        self.x += self.dx
        self.y += self.dy

        # draw ball
        cv2.circle(img, (self.x, self.y), self.r, self.color, -1)
        return (img, self.x, self.y)

class BallVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated bouncing ball.
    """

    def __init__(self):
        super().__init__()
        # generate ball
        self.ball = BouncingBall()
        

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        img, x, y = self.ball.move()
        frame = VideoFrame.from_ndarray(img, format='bgr24')
        frame.pts = pts
        frame.time_base = time_base
        return frame



async def run(pc, signaling):
    

    # connect signaling
    await signaling.connect()

    # send offer
    pc.addTrack(BallVideoStreamTrack())
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bouncing Ball - server")
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