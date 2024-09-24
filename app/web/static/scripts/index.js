var socket = io();
socket.on('connect', function() {
    socket.emit('hello', {data: 'I\'m connected!'});
});
socket.on('frame', function(data) {
    image_arr = new Uint8Array(data.bytes);
    console.log(image_arr)

    let canvas = document.getElementById('outputCanvas');
    let ctx = canvas.getContext('2d');

    canvas.width = data.shape[1];
    canvas.height = data.shape[0];

    let imgData = ctx.createImageData(canvas.width, canvas.height);

    for (let i = 0; i < image_arr.length; i+=3) {
        i4 = i/3*4
        imgData.data[i4] = image_arr[i+2];
        imgData.data[i4+1] = image_arr[i+1];
        imgData.data[i4+2] = image_arr[i];
        imgData.data[i4+3] = 255;
    }

    ctx.putImageData(imgData, 0, 0);
})