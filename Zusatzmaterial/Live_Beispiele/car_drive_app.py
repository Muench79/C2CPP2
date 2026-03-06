# -*- coding: utf-8 -*-

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

# Pfad ermitteln
PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0], '')

# Name der Konfigurationsdatei
CONFIG_FILE_NAME = 'config.json'

# Pfad für den Zugriff auf die Konfigurationsdatei
CONFIG_FILE_PATH = PATH + CONFIG_FILE_NAME       

# WLAN power-save deaktivieren
os.system('sudo iw dev wlan0 set power_save off')

# Logger erstellen
logger = logging.getLogger()

# Debug Level setzen
logger.setLevel(logging.DEBUG)

# Log-Handler für Konsolenausgabe erstellen
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatierungseinstellungen für die Konsolenausgaben erstellen
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.CRITICAL)

# Log-Handler für log.log Datei erstellen
file_handler = logging.FileHandler(os.path.join(PATH, 'log.log'), mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.CRITICAL)

# Handler hinzufügen
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def log_message(level, message, **kwargs):
    # Formatrierung und Meldungen erstellen
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

# Bilder speichern
images_store = False

# Daten für Dateiaufzeichnung
run_name = 'unnamed'
run_id = str(uuid.uuid4())[:8]
image_counter = 1

stop_drive = False
# Konfigurationsdaten einlesen
try:
    with open(CONFIG_FILE_PATH, 'r', encoding="utf-8") as f:
        # Daten einlesen
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
    cropp_img.set_ns(data['Cropp']['ns'])
    cropp_img.set_we(data['Cropp']['we'])
    # Offset
    offset = data['Offset']
    offset_line = data['Offset_Line']
    # Bildgröße für Neuronales Netz
    NEURAL_NETWORK_IMAGE_SIZE = data['Neural-Network']['ImgSize']
    # Neuronales Netz eingeschaltet
    neural_network_use = data['Neural-Network']['Use']
except:
    # HSV Filter erstellen
    hsv_range = HSVRange((78, 138, 28), (132, 255, 255))
    # Zuschneideobjekt erstellen
    cropp_img = Cropp()
    cropp_img.set_ns([35, 80])
    cropp_img.set_we([0, 100])
    # Offset
    offset = 70
    offset_line = 120
    # Bildgröße für neuronalse Netz
    NEURAL_NETWORK_IMAGE_SIZE = (108, 108)
    # Neuronales Netz eingeschaltet
    neural_network_use = False
    data = {}
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
    # Daten für Neuronales Netz
    data['Neural-Network'] = {'ImgSize' : NEURAL_NETWORK_IMAGE_SIZE,
                              'Use' : False} 
# Dash Stylesheet setzen
external_stylesheets = [dbc.themes.DARKLY]
server = Flask(__name__)

# Kamera initialisieren
cam = Camera()

# Dash app erzeugen
app = Dash(external_stylesheets=external_stylesheets, server=server)

def generate_stream(cam):
    global cropped_rgb, offset, offset_line, run_name, run_id, image_counter, stop_drive, NEURAL_NETWORK_IMAGE_SIZE, neural_network_use, images_store
    # Initialisierung
    # Fahrt stoppen
    stop_drive = False
    # Spurerkennung
    track_detection = TrackDetection(cluster_size=5, cluster_distance=50)
    # Linke Spur
    pos_left = False
    # Rechte Spur
    pos_right = False
    # Initialisierung des neuronalen Netzes
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
        if neural_network_use == True:
            # Initialisierung des neuronalen Netzes
            if not neural_network_init:
                # Neuronales Netz wurde noch nicht initialisiert
                # Daten aus trainiertem Netz laden
                interpreter = tflite.Interpreter(model_path=PATH + 'live_model_tflite_nvidia_img.tflite')
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                interpreter.allocate_tensors()
                # Initialisierung abgeschlossen (nur einmalig)
                neural_network_init = True
            # Bildgröße anpassen
            img = cv2.resize(resized, NEURAL_NETWORK_IMAGE_SIZE)
            # Bildpixel von 0-255 auf 0-1 umrechnen
            img = np.asarray(img) / 255
            # Gleitkommazahlgenauigkeit von 64 Bit auf 32 Bit umwandeln (benötigt tflite)
            img = np.float32(img)
            # Eine Achse hinzufügen
            img = np.expand_dims(img, axis=0)
            # Bild übergeben
            interpreter.set_tensor(input_details[0]['index'], img)
            # Berechnung anstoßen
            interpreter.invoke()
            # Ergebnis (Lenkwinkel) speichern
            output_data = interpreter.get_tensor(output_details[0]['index'])
            # Lenkwinkel des Autos setzen
            car.steering_angle = int(output_data[0][0])
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
            # Auto stoppen
            car.drive2(0)
        if car.speed > 0 and images_store:
            # Bildaufzeichnung aktiviert und das Auto fährt
            if not os.path.exists(os.path.join(PATH, 'img')):
                # Ordner existiert nicht -> erstellen
                os.mkdir(os.path.join(PATH, 'img'))
            # Datum und Uhrzeit erstellen
            current_time = datetime.now().strftime("%Y%m%d_%H-%M-%S")
            # Dateiname erstellen
            filename = "IMG_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.jpg".format(
                    run_name, run_id, current_time, image_counter, car.speed, car.steering_angle)
            # Bild speichern
            cv2.imwrite(os.path.join(PATH, 'img', filename), resized)
            # Dateiname erstellen
            filename = "IMG_RAW_{}_{}_{}_{:04d}_S{:03d}_A{:03d}.jpg".format(
                    run_name, run_id, current_time, image_counter, car.speed, car.steering_angle)
            # Bild speichern
            cv2.imwrite(os.path.join(PATH, 'img', filename), frame)
            # Bildzähler erhöhen
            image_counter += 1
        # Messlinien einzeichnen
        cv2.line(cropped_rgb, (0, measuring_offset), (w, measuring_offset), (0, 0, 255), 3)
        cv2.line(resized, (0, measuring_offset), (w, measuring_offset), (0, 0, 255), 3)
        
        cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)

        if track_detection.count == 2:
            # Es werden zwei Spuren erkannt
            # Spurmitte einzeichnen
            cv2.line(cropped_rgb, (center_inner, 0), (center_inner, h), (0, 255, 255), 3)
            cv2.line(resized, (center_inner, 0), (center_inner, h), (0, 255, 255), 3)
        # Bildmitte einzeichnen
        cv2.line(cropped_rgb, (center_image, 0), (center_image, h), (255, 0, 255), 3)
        cv2.line(resized, (center_image, 0), (center_image, h), (255, 0, 255), 3)
        # Bild zum jpeg-Frame umwandeln und zurückgeben
        _, frame_as_jpeg = cv2.imencode(".jpeg", resized)
        frame_in_bytes = frame_as_jpeg.tobytes()
        frame_as_string = (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_in_bytes + b'\r\n\r\n'
            )
        yield frame_as_string

def generate_stream_2():
    global cropped_rgb
    while True:
        # prüfen, ob die Variable existiert
        if "cropped_rgb" not in globals():
            # Variable existiert noch nicht -> Ersatzbild ausgeben
            cropped_rgb = np.zeros((480, 640, 3), dtype=np.uint8)

        # Bild zum jpeg-Frame umwandeln und zurückgeben
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

    # Titelzeile
    dbc.Row([
        dbc.Col([
            html.Div(id="dummy-output", style={"display": "none"}),
            html.H1("Car-Drive-App V1.0.0"),
        ], width=12)
    ]),

    # Videostreams nebeneinander
    dbc.Row([
        dbc.Col([
            html.Img(src="/video_stream", style={"width": "100%", "height": "auto"})
        ], width=6),

        dbc.Col([
            html.Img(src="/video_stream_2", style={"width": "100%", "height": "auto"})
        ], width=6),
    ]),

    # Zweite Spalte rechts
    dbc.Row([
        dbc.Col([
            html.P("Test", id="test"),
        ], width=12)
    ]),

    # Slider-Bereich
    dbc.Row([
        dbc.Col([
            html.P('H', id="h_range"),
            dcc.RangeSlider(id="slider-h", min=0, max=180,
                            value=[hsv_range.lb[0].item(), hsv_range.ub[0].item()]),

            html.P('S', id="s_range"),
            dcc.RangeSlider(id="slider-s", min=0, max=255,
                            value=[hsv_range.lb[1].item(), hsv_range.ub[1].item()]),

            html.P('V', id="v_range"),
            dcc.RangeSlider(id="slider-v", min=0, max=255,
                            value=[hsv_range.lb[2].item(), hsv_range.ub[2].item()]),

            html.P('Oben, Unten', id="cr_ns"),
            dcc.RangeSlider(id="slider-ns", min=0, max=100, value=cropp_img.ns),

            html.P('Links, Rechts', id="cr_we"),
            dcc.RangeSlider(id="slider-we", min=0, max=100, value=cropp_img.we),

            html.P('Geschwindigkeit', id="car_speed"),
            dcc.Slider(id="slider-speed", min=0, max=50, value=0),
        ], width=6)
    ]),

    # Stopp-Button
    dbc.Row([
        dbc.Col([
            dbc.Button("Stopp", id="btn_stop", color="primary")
        ], width=12)
    ]),

    # Werte speichern Button
    dbc.Row([
        dbc.Col([
            dbc.Button("Werte speichern", id="btn_store", color="primary")
        ], width=12)
    ]),

    # Eingabefeld + Checkbox in EINER Zeile direkt nebeneinander
    dbc.Row([
        dbc.Col(
            dcc.Input(
                id="run-ID",
                type="text",
                placeholder="Lauf Name eingeben...",
                value="",
                style={"width": "100%"}
            ),
            width=8
        ),
        dbc.Col(
            dcc.Checklist(
                id="images-checkbox",
                options=[{"label": "Bilder aufnehmen", "value": "on"}],
                value=[],
                style={"margin-top": "6px"}  # optisch auf gleiche Höhe bringen
            ),
            width=4
        )
    ], align="center"),

    # NN-Checkbox
    dbc.Row([
        dbc.Col([
            dcc.Checklist(
                id="nn-checkbox",
                options=[{"label": "Neuronales Netz", "value": "on"}],
                value=['on'] if neural_network_use else []
            )
        ], width=12)
    ])

])

@app.callback(
    Output("test", "children"),
    Output("h_range", "children"),
    Output("s_range", "children"),
    Output("v_range", "children"),
    Output("cr_ns", "children"),
    Output("cr_we", "children"),
    Output("car_speed", "children"),
    Input("slider-h", "value"),
    Input("slider-s", "value"),
    Input("slider-v", "value"),
    Input("slider-ns", "value"),
    Input("slider-we", "value"),
    Input("slider-speed", "value"),
)
def update_p(value_h, value_s, value_v, value_ns, value_we, value_speed):
    global stop_drive
    # Werte übernehmen bzw. setzen
    # HSV-Bereich
    hsv_range.lower_bound([value_h[0], value_s[0], value_v[0]])
    hsv_range.upper_bound([value_h[1], value_s[1], value_v[1]])
    # Zuschneidedaten
    cropp_img.set_ns(value_ns)
    cropp_img.set_we(value_we)
    if int(value_speed) > 0:
        # Auto fährt
        # Fahrstopp aufheben
        stop_drive = False
    # Geschwindigkeit
    car.drive2(int(value_speed))
    # Rückgabe aller Werte
    return_value = (f"Die Einstellungen sind: {value_h}, {value_s}, {value_v}, \n{value_ns}, {value_we}",
                    f"H {value_h[0]} - {value_h[1]}",
                    f"S {value_s[0]} - {value_s[1]}",
                    f"V {value_v[0]} - {value_v[1]}",
                    f"Zuschneiden: Oben {value_ns[0]}%, Unten {value_ns[1]}%",
                    f"Zuschneiden: Links {value_we[0]}%, Rechts {value_we[1]}%",
                    f"Geschwindigkeit {int(value_speed)}")
    return return_value

@app.callback(
    Output('slider-speed', 'value'),
    Input("btn_stop", "n_clicks"),
)
def handle_click_drive_stop(value):
    global stop_drive
    # Fahrstopp setzen
    stop_drive = True
    return 0

@app.callback(
    Output('dummy-output', 'children'),
    Input("btn_store", "n_clicks"),
    prevent_initial_call=True
)
def handle_click_store_values(value):
    global hsv_range, cropp_img, offset, offset_line, data, neural_network_use
    # Daten speichern
    try:
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
        # Daten für Neuronales Netz
        data['Neural-Network'] = {'ImgSize' : NEURAL_NETWORK_IMAGE_SIZE,
                                    'Use' : neural_network_use}
        # Daten in die Konfigurationsdatei schreiben
        with open(CONFIG_FILE_PATH, 'w', encoding="utf-8") as f:    
            json.dump(data, f, indent=4)
    except Exception as e:
        # Fehler beim Speicher aufgetreten
        log_message('ERROR', 'Daten konnten nicht gespeichert werden', CONFIG_FILE_PATH=CONFIG_FILE_PATH, error=e)
    return ""

@app.callback(
    Output('dummy-output', 'children', allow_duplicate=True),
    Input('images-checkbox', 'value'),
    prevent_initial_call=True
)
def images_ceckbox(value):
    global images_store
    if len(value) == 1:
        # Neuronales Netz wird benutzt
        images_store = True
    else:
        # Neuronales Netz wird nicht benutzt
        images_store = False
    return ""

@app.callback(
    Output('dummy-output', 'children', allow_duplicate=True),
    Input('nn-checkbox', 'value'),
    prevent_initial_call=True
)
def nn_ceckbox(value):
    global neural_network_use
    if len(value) == 1:
        # Neuronales Netz wird benutzt
        neural_network_use = True
    else:
        # Neuronales Netz wird nicht benutzt
        neural_network_use = False
    return ""

@app.callback(
    Output('dummy-output', 'children', allow_duplicate=True),
    Input('run-ID', 'value'),
    prevent_initial_call=True
)
def input_run_id(value):
    global run_name
    # Lauf Name setzen
    run_name = value
    return ""

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", debug=False)
    except:
        car.drive2(0)
    car.drive2(0)
    logging.shutdown()