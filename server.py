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
    """
    A class of bouncing ball image

    Attributes:
        height(int): image height
        width(int): image width
        coords([int,int]): coordination of the ball
        r(int): ball radius
        dx(int): ball movement in x-axis
        dy(int): ball movement in y-axis
        color((int,int,int)): color of the ball in BGR format

    """
    def __init__(self):
        """
        Initializing the bouncing ball
        """
        self.height = 240
        self.width = 320
        self.coords = [11,11]
        self.r = 10
        self.dx = 3
        self.dy = 3
        self.color = (255, 255, 255)

    def isCrossingBound(self, coord, max):
        """
        Check if the ball is crossing the bound

        Parameters:
            coord(int): current x-coord or y-coord of the ball
            max(int): the maximum value of axis, generally, it's either self.height or self.width
        """
        if coord-self.r <= 0 or coord+self.r >= max:
            return True
        
        return False
    
    def move(self):
        """
        Return the repaint image after moving the ball
        """
        # black background
        img = numpy.zeros((self.height, self.width, 3), dtype='uint8')

        # switching direction if crossing bounds
        if self.isCrossingBound(self.coords[0], self.width):
            self.dx *= -1
        if self.isCrossingBound(self.coords[1], self.height):
            self.dy *= -1
        
        # move
        self.coords[0] += self.dx
        self.coords[1] += self.dy

        # draw ball
        cv2.circle(img, self.coords, self.r, self.color, -1)
        return img

class BallVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated bouncing ball.
    """

    def __init__(self, ball):
        """
        Initialize ball video stream track
        """
        super().__init__()
        # generate ball
        self.ball = ball
        

    async def recv(self):
        """
        Receive the next video frame.
        repaint the image with ball.move() then return the frame
        """
        pts, time_base = await self.next_timestamp()
        img = self.ball.move()
        frame = VideoFrame.from_ndarray(img, format='bgr24')
        frame.pts = pts
        frame.time_base = time_base
        return frame

def computeError(coords, actual):
    """
    Compute the difference of two coordination
    """
    errX = actual[0] - int(coords[0])
    errY = actual[1] - int(coords[1])
    return (errX, errY)


async def run(pc, signaling):

    # connect signaling
    await signaling.connect()

    pc.createDataChannel('server')
    ball = BouncingBall()

    # recieving data
    @pc.on("datachannel")
    def on_datachannel(channel):
        # print('Channel %s' % channel)
        @channel.on("message")
        def on_message(message):
            if(message.startswith("[coords]:")):
                coords = message.split(":")[1].split(",")
                err = computeError(coords, ball.coords)
                print("Actual (%3d,%3d), Recieved (%3d,%3d), Error (%3d,%3d)" 
                % (ball.coords[0], ball.coords[1], int(coords[0]), int(coords[1]), err[0], err[1]))

    # send offer
    pc.addTrack(BallVideoStreamTrack(ball))
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