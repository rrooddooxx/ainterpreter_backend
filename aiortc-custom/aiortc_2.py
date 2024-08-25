import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import subprocess
import asyncio
import fractions
import cv2
import wave
import numpy as np
from asyncio import Queue
from aiohttp import web
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from av import VideoFrame, AudioFrame
from av.audio.resampler import AudioResampler

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()
relay = MediaRelay()
ffmpeg_process = None        
frame_queue = Queue(maxsize=10)  


class MediaTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"


    def __init__(self, track, audio_transform=None, video_transform=None):
        super().__init__()  # don't forget this!
        self.track = track
        self.video_transform = video_transform
        self.audio_transform = audio_transform

    async def recv(self):
        frame = await self.track.recv()

        if isinstance(frame, VideoFrame):
        # Video frame processing
            return frame
        elif isinstance(frame, AudioFrame):
            if self.audio_transform == "opus_to_pcm":
                pcm_data = frame.to_ndarray()
            
                # Create a new AudioFrame from the decoded PCM data
                new_audio_frame = AudioFrame.from_ndarray(pcm_data, format='s16')
                new_audio_frame.sample_rate = frame.sample_rate
                new_audio_frame.time_base = frame.time_base
                new_audio_frame.pts = frame.pts

                return new_audio_frame
            else:
                return frame
        else:
            return frame

def start_ffmpeg_process():
    global ffmpeg_process
    ffmpeg_command = [
        'ffmpeg',
        '-y',  # overwrite output files
        '-re',
        '-f', 's16le',  # input format for audio
        '-ac', '2',  # number of audio channels
        '-ar', '48000',  # sample rate
        '-i', '-',  # audio input from stdin
        '-bufsize', '512k',  # Increase buffer size
        '-c:a', 'aac',  # audio codec
        '-b:a', '64k',  # set audio bitrate
        '-f', 'rtsp',  # output format
        '-rtsp_transport', 'tcp',  # Specify RTSP transport protocol (TCP)
        'rtsp://localhost:8554/test',  # RTSP server URL
    ]

    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "silence.wav"), loop=True)
    recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

        async def send_pings():
            while True:
                if pc.connectionState in ["connected", "completed"]:
                    channel.send("ping")
                await asyncio.sleep(10)  # Ping every 10 seconds
        
        asyncio.ensure_future(send_pings())

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)


        # Handle ICE state change
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        log_info("ICE connection state is %s", pc.iceConnectionState)
        if pc.iceConnectionState == "closed" or pc.iceConnectionState == "disconnected":
            log_info("ICE connection state is %s, attempting to restart ICE", pc.iceConnectionState)

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            print("Received Audio Track")
            relayed_track = relay.subscribe(track)
            audio_transform_track = MediaTransformTrack(relayed_track, audio_transform="opus_to_pcm")
            asyncio.ensure_future(run_ffmpeg(audio_transform_track))
            # pc.addTrack(player.audio)
            # recorder.addTrack(relayed_track)

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)



    async def run_ffmpeg(track):
        # this works!
        global ffmpeg_process

        if not ffmpeg_process:
            start_ffmpeg_process()

        while True:
            try:
                new_track = await track.recv()

                if isinstance(new_track, AudioFrame):
                    # Convert the AudioFrame to a NumPy array (PCM data)
                    pcm_data = new_track.to_ndarray()

                    # Write the PCM data to ffmpeg's stdin
                    ffmpeg_process.stdin.write(pcm_data.tobytes())

                    # Add a small delay to help manage buffering
                    await asyncio.sleep(0.006)  # Adjust the delay as needed

            except Exception:
                print("MediaStreamError: Track has ended or encountered an issue.")
                break
    
    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()
    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

def stop_ffmpeg_process():
    global ffmpeg_process
    if ffmpeg_process is not None:
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
        ffmpeg_process = None


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    stop_ffmpeg_process()
    pcs.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC audio / video / data-channels demo"
    )
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8081, help="Port for HTTP server (default: 8081)"
    )
    parser.add_argument("--record-to", help="Write received media to a file.")
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(
        app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    )
