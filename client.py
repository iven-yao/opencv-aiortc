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

class CustomVideoStreamTrack(MediaStreamTrack):
    kind = "video"
    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        return frame
    
async def FrameTransport(pc, track):
    videoStream = CustomVideoStreamTrack(track)

    while True:
        try:
            frame = await videoStream.recv()
            img = frame.to_ndarray(format='bgr24')
            cv2.imshow("Server generated stream", img)
            cv2.waitKey(1)
        except Exception:
            pass

async def run(pc, signaling):

    @pc.on("track")
    async def on_track(track):
        print("Receiving %s" % track.kind)
        await FrameTransport(pc, track)

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
        loop.run_until_complete(cv2.destroyAllWindows())