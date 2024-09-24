from flask import Flask, render_template, send_from_directory, Response
from os import listdir
from os.path import isfile, join
from time import sleep, time
# from flask_socketio import SocketIO, emit
import socketio
from psutil import cpu_percent
import cv2
import asyncio
from aiohttp import web

FRAMETIME = 1/15

web_path = '/users/root/app/web/'
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
            frame = image.tobytes()
            await sio.emit('frame', {'bytes': frame, 'shape': images[0].shape}, room='video') 
            frame_times.append(time() - frame_start)
            await sio.sleep(0.1)
            # if sleep_time := frame_start + FRAMETIME - time() > 0:
            #     await sio.sleep(sleep_time)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5050)