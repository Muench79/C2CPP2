from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, Response
from basisklassen_cam import Camera
import cv2
import numpy as np
import sys
import pprint
import json
import math
from basecar import BaseCar
import os
import time
from hsvrange import HSVRange
from cropp import Cropp
import requests
from trackdetection import TrackDetection
import uuid
from datetime import datetime
import logging
import tflite_runtime.interpreter as tflite
 
#-runtime.interpreter as ftlite

# Pfad ermitteln
PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0], '')

# Name der Konfigurationsdatei
CONFIG_FILE_NAME = 'config.json'

# Pfad für den Zugriff auf die Konfigurationsdatei
CONFIG_FILE_PATH = PATH + CONFIG_FILE_NAME       

# Bildgröße für NN
IMG_SIZE = (224, 224)

# WLAN power-save deaktivieren
os.system('sudo iw dev wlan0 set power_save off')

# create logger
logger = logging.getLogger()
#logging.getLogger("dash.dash").disabled = True

logger.setLevel(logging.DEBUG)

# create log handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# create format handler (console)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.CRITICAL)

# create format handler (file)
file_handler = logging.FileHandler(os.path.join(PATH, 'log.log'), mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# add handler
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def log_message(level, message, **kwargs):
    # Format and generate log message
    param_str = ' | '.join(f'{key}={value}' for key, value in kwargs.items())
    full_message = f'{message} | {param_str}' if param_str else message

    if level == 'DEBUG':
        logger.debug(full_message)
    elif level == 'INFO':
        logger.info(full_message)
    elif level == 'WARNING':
        logger.warning(full_message)
    elif level == 'ERROR':
        logger.error(full_message)
    elif level == 'CRITICAL':
        logger.critical(full_message)
    else:
        logger.info(f'Unbekannter Loglevel \'{level}\': {full_message}')

# Auto Objekt erstellen
car = BaseCar()
car.steering_angle = 90 # Lenkung gerade
car.drive2(0) # Geschwindigkeit 0

# Daten für Dateiaufzeichnung
run_name = "SRC"
run_id = str(uuid.uuid4())[:8]
image_counter = 1

stop_drive = False
# Konfigurationsdaten einlesen
try:
    with open(CONFIG_FILE_PATH, 'r', encoding="utf-8") as f:
        data = json.load(f)
    # HSV Filter erstellen
    hsv_range = HSVRange((data['HSV-Filter']['h_min'],
                                data['HSV-Filter']['s_min'],
                                data['HSV-Filter']['v_min']),
                               (data['HSV-Filter']['h_max'],
                                data['HSV-Filter']['s_max'],
                                data['HSV-Filter']['v_max']))
    # Zuschneideobjekt erstellen
    cropp_img = Cropp()
    print(data['Cropp']['ns'])
    cropp_img.set_ns(data['Cropp']['ns'])
    cropp_img.set_we(data['Cropp']['we'])
    # Offset
    offset = data['Offset']
    offset_line = data['Offset_Line']
    neural_network = data['Neural-Network']
except:
    # HSV Filter erstellen
    hsv_range = HSVRange((100, 150, 50), (140, 255, 255))
    # Zuschneideobjekt erstellen
    cropp_img = Cropp()
    cropp_img.set_ns([35, 90])
    cropp_img.set_we([0, 100])
    # Offset
    offset = 50
    offset_line = 1000
    data = {}
    neural_network = False



# Dash Stylesheet setzen
external_stylesheets = [dbc.themes.DARKLY]
server = Flask(__name__)

# Kamera initialisieren
cam = Camera()

# Dash app erzeugen
app = Dash(external_stylesheets=external_stylesheets, server=server)

logging.getLogger("dash").setLevel(logging.WARNING)
logging.getLogger("dash.dash").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

def generate_stream(cam):
    global cropped_rgb, offset, offset_line, run_name, run_id, image_counter, stop_drive, IMG_SIZE, neural_network
    stop_drive = False
    track_detection = TrackDetection(cluster_size=5, cluster_distance=50)
    pos_left = False
    pos_right = False
    neural_network_init = False
    while True:
        # Kamerabild einlesen
        frame = cam.get_frame()
        # Bild auf die Hälfte verkleinern
        resized = cv2.resize(frame, None, fx=0.5, fy=0.5)
        # HSV Bild erzeugen (BGR -> HSV)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        # Farbe über HSV-Filter filtern 
        filtered = cv2.inRange(hsv, hsv_range.lowerbound, hsv_range.upperbound)
        # Größe des Bildes ermitteln
        h, w = filtered.shape
        # Farbbild zuschneiden
        resized = resized[int(cropp_img.ns[0]*0.01*h):int(cropp_img.ns[1]*0.01*h),
                        int(cropp_img.we[0]*0.01*w):int(cropp_img.we[1]*0.01*w):]
        # Gefiltertes Bild zuschneiden
        cropped = filtered[int(cropp_img.ns[0]*0.01*h):int(cropp_img.ns[1]*0.01*h),
                        int(cropp_img.we[0]*0.01*w):int(cropp_img.we[1]*0.01*w):]
        # Messoffset berechnen (immer Bildhöhe - Offset)
        measuring_offset = resized.shape[0] - offset
        
        # Größe des Bildes ermitteln
        h, w, c = resized.shape
        # Bildmitte berechnen
        center_image = int(w/2)
        #print(neural_network)
        if neural_network == True:
            if not neural_network_init:
                interpreter = tflite.Interpreter(model_path=PATH + 'live_model_tflite.tflite')
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                interpreter.allocate_tensors()
                neural_network_init = True
            img = frame[:,:,::-1]
            img = cv2.resize(img, IMG_SIZE)
            
            img = np.asarray(img) / 255
            img = np.float32(img)
            img = np.expand_dims(img, axis=0)
            try:
               interpreter.set_tensor(input_details[0]['index'], img)
            except Exception as e:
               print(e)
            
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_details[0]['index'])
            print('Outputdata', output_data[0][0])
            car.steering_angle = int(output_data[0][0])
            #print(input_details)
            #print(output_details)
            #print(img.shape, img.dtype)

            #print("int(output_data)")
        else:         
            # Spurerkennung
            track_detection.center(center_image)
            track_detection.row(cropped[measuring_offset])
            
            if track_detection.count == 2:
                # Zwei Spuren erkannt
                # Spurpositionen löschen
                pos_left = False
                pos_right = False
                # Mittelpunkt der Spuren berechnen
                center_inner = int(track_detection.x_left_inner + track_detection.distance_inner / 2) 
                # Abweichung bzw. Differenz ermitteln
                diff = center_image - center_inner
                # Lenkwinkel berechnen
                grad = int(math.degrees(math.atan2(offset, diff)) )
                # Lenkwinkel setzen
                car.steering_angle = grad
                log_message('DEBUG', 'Beide linien erkannt', offset=offset, diff=diff, grad=grad, steering_angle=car.steering_angle, run_name=run_name, run_id=run_id, image_counter=image_counter)      
            elif track_detection.count == 1:
                # Nur eine Spur erkannt
                # Position (1 = links, 2 = recht) ermitteln
                position = track_detection.position
                if (position == 1 or pos_left) and not pos_right:
                    # Linke Spur
                    pos_left = True
                    # Abweichung berechnen
                    diff = ((center_image - offset_line) - track_detection.x_2)
                    # Lenkwinkel berechen
                    grad = int(math.degrees(math.atan2(offset, diff)))
                    # Lenkwinkel setzen
                    car.steering_angle = grad
                    log_message('DEBUG', 'Nur linke Linie erkannt', offset=offset, diff=diff, grad=grad, steering_angle=car.steering_angle, run_name=run_name, run_id=run_id, image_counter=image_counter)
                elif (position == 2 or pos_right) and not pos_left:
                    # Rechte Spur
                    pos_right = True
                    # Abweichung berechnen
                    diff = ((center_image + offset_line) - track_detection.x_1)
                    # Lenkwinkel berechen
                    grad = int(math.degrees(math.atan2(offset, diff)))
                    # Lenkwinkel setzen
                    car.steering_angle = grad
                    log_message('DEBUG', 'Nur rechte Linie erkannt', offset=offset, diff=diff, grad=grad, steering_angle=car.steering_angle, run_name=run_name, run_id=run_id, image_counter=image_counter)
            else:
                log_message('DEBUG', 'Keine Linien erkannt', offset=offset, steering_angle=car.steering_angle, run_name=run_name, run_id=run_id, image_counter=image_counter)
        if stop_drive:
            car.drive2(0)
        if car.speed > 0:
            current_time = datetime.now().strftime("%Y%m%d_%H-%M-%S")
            filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.png".format(
                    run_name, run_id, current_time, image_counter, car.speed, car.steering_angle)
            cv2.imwrite(os.path.join(PATH, 'img', filename), resized)
            filename = "IMG_RAW_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.png".format(
                    run_name, run_id, current_time, image_counter, car.speed, car.steering_angle)
            cv2.imwrite(os.path.join(PATH, 'img', filename), frame)
            image_counter += 1
        
            cv2.line(cropped_rgb, (0, measuring_offset), (w, measuring_offset), (0, 0, 255), 3)
            cv2.line(resized, (0, measuring_offset), (w, measuring_offset), (0, 0, 255), 3)
        #print('Result',angle.result[1])
        cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)

        if track_detection.count == 2:
            cv2.line(cropped_rgb, (center_inner, 0), (center_inner, h), (0, 255, 255), 3)
            cv2.line(resized, (center_inner, 0), (center_inner, h), (0, 255, 255), 3)
        cv2.line(cropped_rgb, (center_image, 0), (center_image, h), (255, 0, 255), 3)
        cv2.line(resized, (center_image, 0), (center_image, h), (255, 0, 255), 3)
        _, frame_as_jpeg = cv2.imencode(".jpeg", resized)

        frame_in_bytes = frame_as_jpeg.tobytes()

        frame_as_string = (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_in_bytes + b'\r\n\r\n')
        yield frame_as_string

def generate_stream_2():
    global cropped_rgb

    while True:
        # prüfen, ob die Variable existiert
        if "cropped_rgb" not in globals():
            cropped_rgb = np.zeros((480, 640, 3), dtype=np.uint8)

        # Frame encodieren
        _, frame_as_jpeg = cv2.imencode(".jpeg", cropped_rgb)
        frame_in_bytes = frame_as_jpeg.tobytes()

        frame_as_string = (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_in_bytes + b'\r\n\r\n'
        )

        yield frame_as_string

@server.route("/video_stream")
def video_stream():
    return Response(generate_stream(cam), mimetype='multipart/x-mixed-replace; boundary=frame')

@server.route("/video_stream_2")
def video_stream_2():
    return Response(generate_stream_2(), mimetype='multipart/x-mixed-replace; boundary=frame')


app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.Div(id="dummy-output", style={"display": "none"}),
            html.H1("Hallo Projektphase"),
            html.P("Test", id="test"),
            html.Div(html.Img(src="/video_stream")),
        ]),
        dbc.Col([
            html.P("Test", id="test_2"),
            html.Div(html.Img(src="/video_stream_2"))
        ]),
        dbc.Col([
            html.P('H'),
            dcc.RangeSlider(id="slider-h", min=0, max=180, value= [hsv_range.lb[0].item(), hsv_range.ub[0].item()]),
            html.P('S'),
            dcc.RangeSlider(id="slider-s", min=0, max=255, value=[hsv_range.lb[1].item(), hsv_range.ub[1].item()]),
            html.P('V'),
            dcc.RangeSlider(id="slider-v", min=0, max=255, value=[hsv_range.lb[2].item(), hsv_range.ub[2].item()]),
            html.P('Oben, Unten'),
            dcc.RangeSlider(id="slider-ns", min=0, max=100, value=cropp_img.ns),
            html.P('Links, Rechts'),
            dcc.RangeSlider(id="slider-we", min=0, max=100, value=cropp_img.we),
            html.P('Geschwindigkeit'),
            dcc.Slider(id="slider-speed", min=0, max=50, value=0),
        ],
        width=6),
        dbc.Row([
            dbc.Col([
                dbc.Button("Stopp", id="btn_stop", color="primary")])
                ]),
        dbc.Row([
            dbc.Col([
                dbc.Button("Werte speichern", id="btn_store", color="primary")]),
                dcc.Checklist(id="nn-checkbox", options=[{"label": "Neuronales Netz", "value": "on"}],
        value=[])
])
        

    ])
    

])

@app.callback(
    Output("test", "children"),
    Input("slider-h", "value"),
    Input("slider-s", "value"),
    Input("slider-v", "value"),
    Input("slider-ns", "value"),
    Input("slider-we", "value"),
    Input("slider-speed", "value"),
)
def update_p(value_h, value_s, value_v, value_ns, value_we, value_speed):
    global stop_drive
    hsv_range.lower_bound([value_h[0], value_s[0], value_v[0]])
    hsv_range.upper_bound([value_h[1], value_s[1], value_v[1]])
    cropp_img.set_ns(value_ns)
    cropp_img.set_we(value_we)

    print(value_speed)
    if int(value_speed) > 0:
        stop_drive = False
    car.drive2(int(value_speed))
    #cropp_img.set_ns(value_ns)
    #cropp_img.set_we(value_we)
    #print(cropp_img.ns, cropp_img.we, 1 - cropp_img.ns[1]*0.01)
    return_value = f"Die Einstellungen sind: {value_h}, {value_s}, {value_v}, \n{value_ns}, {value_we}"
    return return_value

@app.callback(
    Output('slider-speed', 'value'),
    Input("btn_stop", "n_clicks"),
)
def handle_click_drive_stop(value):
    global stop_drive
    stop_drive = True
    return 0

@app.callback(
    Output('dummy-output', 'children'),
    Input("btn_store", "n_clicks"),
)
def handle_click_store_values(value):
    global hsv_range, cropp_img, offset, offset_line, data
    with open(CONFIG_FILE_PATH, 'w', encoding="utf-8") as f:
        # HVS-Filter
        data['HSV-Filter'] = {'h_min' : int(hsv_range.lb[0]),
                              'h_max' : int(hsv_range.ub[0]),
                              's_min' : int(hsv_range.lb[1]),
                              's_max' : int(hsv_range.ub[1]),
                              'v_min' : int(hsv_range.lb[2]),
                              'v_max' : int(hsv_range.ub[2])}
        # Zuschneideobjekt
        data['Cropp'] = {'ns' : cropp_img.ns,
                         'we' : cropp_img.we}
        # Offset
        data['Offset'] = offset
        # Lineoffset
        data['Offset_Line'] = offset_line
        # Daten in die Konfigurationsdatei schreiben
        json.dump(data, f, indent=4)
    return ""
@app.callback(
    Output('dummy-output', 'children', allow_duplicate=True),
    Input('nn-checkbox', 'value'),
    prevent_initial_call=True
)
def nn_ceckbox(value):
    global neural_network
    if len(value) == 1:
        neural_network = True
    else:
        neural_network = False
    return ""

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", debug=False)
    except:
        car.drive2(0)
    car.drive2(0)
    logging.shutdown()
# sudo shutdown -h now