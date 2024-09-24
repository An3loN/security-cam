from flask import Flask, render_template, send_from_directory, Response
from os import listdir
from os.path import isfile, join
from time import sleep, time
from flask_socketio import SocketIO, emit
from psutil import cpu_percent
import cv2

FRAMETIME = 1/15

web_path = '/users/root/app/web/'
images_path = web_path + 'images/'
app = Flask(__name__, static_folder=web_path+'static/')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
image_files = [f for f in listdir(images_path) if isfile(join(images_path, f))]

images = [cv2.imread(images_path + file) for file in image_files]

print('target frame time: ', FRAMETIME)

cpu_load_stamps = []
frame_times = []
start_time = None

def generate():
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
            emit('frame', {'bytes': frame, 'shape': images[0].shape}) 
            frame_times.append(time() - frame_start)
            # if sleep_time := frame_start + FRAMETIME - time() > 0:
            #     await asyncio.sleep(sleep_time)

@socketio.on('connect')
def on_connect(data):
    emit('frame', {'bytes': images[0].tobytes(), 'shape': images[0].shape})
    sleep(1)
    emit('frame', {'bytes': images[1].tobytes(), 'shape': images[1].shape})
    sleep(1)
    emit('frame', {'bytes': images[2].tobytes(), 'shape': images[2].shape})
    

@app.route("/")
def hello_world():
    return render_template('index.html')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    socketio.run(app, host='0.0.0.0', port=5050)

# def somefunc():
#     data = get_updated_data()
#     emit('data', data)