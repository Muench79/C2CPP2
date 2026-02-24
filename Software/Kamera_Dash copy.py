from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, Response
from basisklassen_cam import Camera
import cv2
import numpy as np

external_stylesheets = [dbc.themes.DARKLY]
server = Flask(__name__)

cam = Camera()

app = Dash(external_stylesheets=external_stylesheets, server=server)

@server.route("/test")
def unterseite_test():
    return "Hier ist die zweite Seite"


def generate_stream(cam):
    while True:
        frame = cam.get_frame()
        resized = cv2.resize(frame, None, fx=0.5, fy=0.5)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        filtered = cv2.inRange(hsv, np.array([90, 0, 0]), np.array([120, 255, 255]))
        h, w = filtered.shape
        cropped = filtered[int(0.35*h):int(0.85*h), :]
        cropped2 = resized[int(0.35*h):int(0.85*h), :]
        print("cropped2", cropped2)
        print("cropped", cropped)
        median_blurred = cv2.medianBlur(cropped, 13)
        edges = cv2.Canny(median_blurred, 100, 200)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=20, minLineLength=20, maxLineGap=10)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(cropped2, (x1, y1), (x2, y2), (0, 255, 0), 2)
                #cv2.line(resized[int(0.35*h):int(0.85*h), :], (x1, y1), (x2, y2), (0, 255, 0), 2)
        print(lines)
        _, frame_as_jpeg = cv2.imencode(".jpeg", cropped2)

        frame_in_bytes = frame_as_jpeg.tobytes()

        frame_as_string = (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_in_bytes + b'\r\n\r\n')
        
        yield frame_as_string


@server.route("/video_stream")
def video_stream():
    return Response(generate_stream(cam), mimetype='multipart/x-mixed-replace; boundary=frame')



app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Hallo Projektphase"),
            html.P("Test", id="test"),
            html.Div(html.Img(src="/video_stream"))
        ]),
        dbc.Col([
            dcc.RangeSlider(id="slider-h", min=0, max=180),
            dcc.RangeSlider(id="slider-s", min=0, max=255),
            dcc.RangeSlider(id="slider-v", min=0, max=255),
        ],
        width=6)
    ])
    

])

@app.callback(
    Output("test", "children"),
    Input("slider-h", "value"),
    Input("slider-s", "value"),
    Input("slider-v", "value"),
)
def update_p(value_h, value_s, value_v):
    return_value = f"Die Einstelungen sind: {value_h}, {value_s}, {value_v}"
    return return_value


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
