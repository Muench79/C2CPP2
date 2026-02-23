from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, Response
from ShowCar.basisklassen_cam import Camera
import cv2
import numpy as np

external_stylesheets = [dbc.themes.BOOTSTRAP]
server = Flask(__name__)

app = Dash(__name__, external_stylesheets=external_stylesheets, server=server)

cam = Camera()


def generate_stream(camera_instance):
    while True:
        frame = camera_instance.get_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray, 100, 200)
        stacked = np.hstack([gray, canny])
        _, x = cv2.imencode(".jpeg", stacked)
        x_bytes = x.tobytes()

        x_string = (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + x_bytes + b'\r\n\r\n')
        
        yield x_string
        

@server.route("/video_feed")
def video_feed():
   return Response(generate_stream(cam), mimetype='multipart/x-mixed-replace; boundary=frame')


# Reine Optik
app.layout = html.Div(children=[
    html.H1("Hallo Projektphase 2"),
    dbc.Row([
        dbc.Col( html.Div([html.Img(src="/video_feed", id="videofeed", style={'height':'200px'})])), 
        dbc.Col([html.H3("Hier wird der Slider Text stehen", id="slider-text"),]),
        dbc.Col([
            dbc.Row([dcc.RangeSlider(id="h-slider", min=0, max=180, value=[20, 50])]),
            dbc.Row([dcc.RangeSlider(id="s-slider", min=0, max=180, value=[20, 50])]),
            dbc.Row([dcc.RangeSlider(id="v-slider", min=0, max=180, value=[20, 50])]),
        
        ])
    ])
    
   
])


# Verbindung Interaktiver Elemente (Slider, Dropdown, usw.) mit Optik über Callbacks
@app.callback(
    # id zum identifizieren, property um zu sagen was genau verändert werden soll (Wert, Farbe, Text)
    Output("slider-text", "children"),
    Input("h-slider", "value")
    )
def update_slider_text(h_slider):
    return f"Untere Grenze {h_slider[0]}, obere Grenze {h_slider[1]}"

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=False, port=8050)