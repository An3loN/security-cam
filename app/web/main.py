from flask import Flask, render_template, send_from_directory, Response
from os import listdir
from os.path import isfile, join
from time import sleep, time
import socketio
from psutil import cpu_percent
import cv2
import asyncio
from aiohttp import web
import numpy as np
import base64

FRAMETIME = 1/15

web_path = '/mnt/d/Projects/Python/practice/app/web/'
images_path = web_path + 'images/'
image_files = [f for f in listdir(images_path) if isfile(join(images_path, f))]
images = [cv2.imread(images_path + file) for file in image_files]

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

print('target frame time: ', FRAMETIME)

cpu_load_stamps = []
frame_times = []
start_time = None

started_stream = False


async def index(request):
    """Serve the client-side application."""
    with open(web_path+'templates/index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

@sio.event
def connect(sid, environ):
    print("connect ", sid)
    loop = asyncio.get_event_loop()
    loop.create_task(sio.enter_room(sid, 'video'))

@sio.event
async def request_video(sid, data):
    print("message ", data)
    global started_stream
    if not started_stream:
        started_stream = True
        asyncio.ensure_future(stream_loop())

@sio.event
def disconnect(sid):
    print('disconnect ', sid)
    loop = asyncio.get_event_loop()
    loop.create_task(sio.leave_room(sid, 'video'))

app.router.add_static('/static', web_path + 'static')
app.router.add_get('/', index)

def compute_orb_keypoints(image):
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(image, None)
    keypoints_data = [(int(kp.pt[0]), int(kp.pt[1])) for kp in keypoints]
    return keypoints_data

def compute_histogram(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    return hist.tolist()

async def stream_loop():
    global start_time
    while True:
        if not start_time:
            start_time = time()
        if time() - start_time >= 10:
            print('average cpu load: ', sum(cpu_load_stamps)/len(cpu_load_stamps))
            print('average frame time: ', sum(frame_times)/len(frame_times))
            cpu_load_stamps.clear()
            frame_times.clear()
            start_time = time()
        for image in images:
            frame_start = time()
            cpu_load_stamps.append(cpu_percent())

            # Extract ORB keypoints and histogram
            keypoints = compute_orb_keypoints(image)
            histogram = compute_histogram(image)

            # Convert image to bytes
            frame = image.tobytes()

            await sio.emit('frame', {
                'bytes': frame,
                'shape': images[0].shape,
                'keypoints': keypoints,
                'histogram': histogram
            }, room='video') 

            frame_times.append(time() - frame_start)
            await sio.sleep(0.1)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5050)
