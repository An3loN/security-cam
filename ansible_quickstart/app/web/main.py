from flask import Flask, send_from_directory, Response
from os import listdir
from os.path import isfile, join
from time import sleep, time
from psutil import cpu_percent
from mjpeg_streamer import MjpegServer, Stream
import cv2

app = Flask(__name__, static_folder='static/')
web_path = '/users/root/app/web/'
images_path = web_path + 'images/'
image_files = [f for f in listdir(images_path) if isfile(join(images_path, f))]

images = [cv2.imread(images_path + file) for file in image_files]

stream = Stream('image_stream', size=(640, 480), fps=15)
server = MjpegServer('0.0.0.0', 8080)
server.add_stream(stream)
server.start()

cpu_load_stamps = []
encode_times = []
frame_times = []
start_time = None

def generate():
    global start_time
    while True:
        if not start_time:
            start_time = time()
        if time() - start_time >= 10:
            print('average cpu load: ', sum(cpu_load_stamps)/len(cpu_load_stamps))
            print('average image encode time: ', sum(encode_times)/len(encode_times))
            print('average frame time: ', sum(frame_times)/len(frame_times))
            cpu_load_stamps.clear()
            encode_times.clear()
            frame_times.clear()
            start_time = time()
        for image in images:
            frame_start = time()
            encode_start = time()
            ret, jpeg = cv2.imencode('.jpg', image)
            encode_times.append(time() - encode_start)
            cpu_load_stamps.append(cpu_percent())
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            frame_times.append(time() - frame_start)

@app.route("/")
def hello_world():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    while True:
        if not start_time:
            start_time = time()
        if time() - start_time >= 10:
            print('average cpu load: ', sum(cpu_load_stamps)/len(cpu_load_stamps))
            print('average image encode time: ', sum(encode_times)/len(encode_times))
            print('average frame time: ', sum(frame_times)/len(frame_times))
            cpu_load_stamps.clear()
            encode_times.clear()
            frame_times.clear()
            start_time = time()
        for image in images:
            frame_start = time()
            encode_start = time()
            stream.set_frame(image)
            encode_times.append(time() - encode_start)
            cpu_load_stamps.append(cpu_percent())
            frame_times.append(time() - frame_start)
