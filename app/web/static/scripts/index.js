var socket = io();
socket.on('connect', function() {
    socket.emit('request_video', {data: 'I\'m connected!'});
});

socket.on('frame', function(data) {
    let image_arr = new Uint8Array(data.bytes);

    let canvas = document.getElementById('outputCanvas');
    let ctx = canvas.getContext('2d');

    canvas.width = data.shape[1];
    canvas.height = data.shape[0];

    let imgData = ctx.createImageData(canvas.width, canvas.height);

    if(data.shape.length < 3) {
        for (let i = 0; i < image_arr.length; i++) {
            let i4 = i*4;
            imgData.data[i4] = image_arr[i];
            imgData.data[i4+1] = image_arr[i];
            imgData.data[i4+2] = image_arr[i];
            imgData.data[i4+3] = 255;
        }
    } else {
        for (let i = 0; i < image_arr.length; i+=3) {
            let i4 = i/3*4;
            imgData.data[i4] = image_arr[i+2];
            imgData.data[i4+1] = image_arr[i+1];
            imgData.data[i4+2] = image_arr[i];
            imgData.data[i4+3] = 255;
        }
    }
    

    ctx.putImageData(imgData, 0, 0);

    // Plot keypoints
    let keypoints = data.keypoints;
    let keypointsCanvas = document.getElementById('keypointsCanvas');
    let keypointsCtx = keypointsCanvas.getContext('2d');

    keypointsCanvas.width = data.shape[1];
    keypointsCanvas.height = data.shape[0];

    keypointsCtx.clearRect(0, 0, keypointsCanvas.width, keypointsCanvas.height);
    keypointsCtx.drawImage(canvas, 0, 0);

    keypointsCtx.fillStyle = 'red';
    keypoints.forEach(([x, y]) => {
        keypointsCtx.beginPath();
        keypointsCtx.arc(x, y, 3, 0, 2 * Math.PI);
        keypointsCtx.fill();
    });

    // Plot histogram using Plotly
    let histogram = data.histogram;
    let trace = {
        x: Array.from({length: 256}, (_, i) => i),
        y: histogram,
        type: 'bar'
    };

    let layout = {
        title: 'Image Histogram',
        xaxis: {title: 'Intensity'},
        yaxis: {title: 'Frequency'}
    };

    Plotly.newPlot('histogramPlot', [trace], layout);
});

window.onload=function(){
    document.getElementById('configUpload').addEventListener('change', function(event) {
        let file = event.target.files[0];
        if (file) {
            let reader = new FileReader();
            reader.onload = function(e) {
                try {
                    let config = JSON.parse(e.target.result);
                    socket.emit('upload_config', {config: e.target.result});
                    console.log('Configuration uploaded:', config);
                } catch (err) {
                    console.error('Invalid configuration file:', err);
                }
            };
            reader.readAsText(file);
        }
    });
}