import json
from time import sleep, time
from dotenv import load_dotenv
import socketio
import os
from psutil import cpu_percent
import cv2
import asyncio
from aiohttp import web
import numpy as np

FRAMETIME = 1/15

load_dotenv()

# web_path = 'D:/Projects/Python/practice/app/web/'
web_path = os.environ['WEB_APP_PATH']

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

image_binary_mode = False
binary_threshold = 128

cam_port = 2
cam = cv2.VideoCapture(cam_port) 

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

@sio.event
async def upload_config(sid, data):
    global image_binary_mode, binary_threshold
    try:
        config = json.loads(data['config'])
        image_binary_mode = config.get('image_binary_mode', False)
        binary_threshold = int(config.get('binary_threshold', 128))
        binary_threshold = max(0, min(255, binary_threshold))  # Clamp to valid range
        print(f"Configuration updated: image_binary_mode={image_binary_mode}, binary_threshold={binary_threshold}")
    except Exception as e:
        print(f"Error processing config: {e}")

app.router.add_static('/static', web_path + 'static')
app.router.add_get('/', index)

def compute_orb_keypoints(image):
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(image, None)
    keypoints_data = [(int(kp.pt[0]), int(kp.pt[1])) for kp in keypoints]
    return keypoints_data

def compute_histogram(image):
    if not image_binary_mode:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    return hist.tolist()

def apply_binary_threshold(image, threshold):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    return binary

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
        for i in range(30):
            frame_start = time()
            result, image = cam.read()
            cpu_load_stamps.append(cpu_percent())
            if not result: continue

            # Apply binary mode if enabled
            if image_binary_mode:
                image_to_send = apply_binary_threshold(image, binary_threshold)
            else:
                image_to_send = image

            # Extract ORB keypoints and histogram
            keypoints = compute_orb_keypoints(image_to_send)
            histogram = compute_histogram(image_to_send)

            # Convert image to bytes
            frame = image_to_send.tobytes()
            await sio.emit('frame', {
                'bytes': frame,
                'shape': image_to_send.shape,
                'keypoints': keypoints,
                'histogram': histogram
            }, room='video') 

            frame_times.append(time() - frame_start)
            await sio.sleep(0.1)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5050)
