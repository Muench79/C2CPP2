from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, Response
from basisklassen_cam import Camera
import cv2
import numpy as np
import sys
external_stylesheets = [dbc.themes.DARKLY]
server = Flask(__name__)

import math


class HSVRange:
    def __init__(self):
        self.lb = np.array([0,0,0])
        self.ub = np.array([0,0,0])
    
    def lower_bound(self, lb):
        self.lb = np.array(lb)

    def upper_bound(self, ub):
        self.ub = np.array(ub)
    
    @property
    def lowerbound(self):
        return self.lb
    
    @property
    def upperbound(self):
        return self.ub

class Cropp:
    def __init__(self):
        self.__ns = [0,100]
        self.__we = [0,100]
    
    def set_ns(self, value):
        self.__ns = value
    
    def set_we(self, value):
        self.__we = value
    
    @property
    def ns(self):
        return self.__ns
    
    @property
    def we(self):
        return self.__we
    


#sys.exit()
def winkel(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    theta = math.atan2(dy, dx)          # Winkel in Radiant
    grad = math.degrees(theta)          # Umrechnung in Grad
    return grad

hsv_range = HSVRange()
cropp_img = Cropp()

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
        
        filtered = cv2.inRange(hsv, hsv_range.lowerbound, hsv_range.upperbound)
        #filtered = cv2.inRange(hsv, np.array([90, 0, 0]), np.array([120, 255, 255]))
        h, w = filtered.shape
        
        offset = 20
        #print(filtered.shape)
        #print('jhjjhhdjfhguhr', cropp_img.ns[0]*0.1)
        #print("Was kommt hier raus?", cropp_img.ns)
        #int(h - (cropp_img.ns[1] * 0.01 * h))
        #resized = resized[int(cropp_img.ns[0]*0.01*h):int(h - (cropp_img.ns[1] * 0.01 * h)), :]
        resized = resized[int(cropp_img.ns[0]*0.01*h):int(cropp_img.ns[1]*0.01*h), int(cropp_img.we[0]*0.01*w):int(cropp_img.we[1]*0.01*w):]
        #cropped = filtered[int(cropp_img.ns[0]*0.01*h):int(h - (cropp_img.ns[1] * 0.01 * h)):, :]
        cropped = filtered[int(cropp_img.ns[0]*0.01*h):int(cropp_img.ns[1]*0.01*h), int(cropp_img.we[0]*0.01*w):int(cropp_img.we[1]*0.01*w):]
        
        h, w, c = resized.shape
        median_blurred = cv2.medianBlur(cropped, 13)
        edges = cv2.Canny(median_blurred, 100, 200)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=20, minLineLength=20, maxLineGap=10)
        
        #cv2.line(resized, (10, 0), (100, 100), (0, 255, 0), 2)

        if lines is not None:
             for line in lines:
                x1, y1, x2, y2 = line[0]
                if x1 > int(w/2):

                    cv2.line(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
                else:
                    cv2.line(resized, (x1, y1), (x2, y2), (0, 255, 255), 2)
                #print(int(winkel(x1,y1,x2,y2)))
                #print(winkel(1,1,1,10))
            if len(linien_rechts_sortiert) > 1 and len(linien_links_sortiert) > 1:
                angle.line_inner_1(*linien_links[-1])
                angle.line_inner_2(*linien_rechts[0])
                angle.line_outer_1(*linien_links[0])
                angle.line_outer_2(*linien_rechts[-1])
                #car.steering_angle = angle.result[0]
        
        row = cropped[messsoffset]
        white_pixels = np.where(row == 255)[0]
        clusters = []
        if len(white_pixels) > 0:
            start = white_pixels[0]
            prev = white_pixels[0]

            for x in white_pixels[1:]:
                if x == prev + 1:
                    prev = x
                else:
                    clusters.append((start, prev))
                    start = x
                    prev = x
            clusters.append((start, prev))

        if len(clusters) == 2:
            x_left_outer = clusters[0][0]
            x_left_inner = clusters[0][1]
            x_right_inner = clusters[1][0]
            x_right_outer = clusters[1][1]

            distance_outer = x_right_outer - x_left_outer
            distance_inner = x_right_inner - x_left_inner
            
            center_outer = int(x_left_outer + distance_outer / 2)
            center_inner = int(x_left_inner + distance_inner / 2)

            diff = abs(center_inner - int(w/2))
            
                     # Winkel in Radiant
            grad = int(math.degrees(math.atan2(offset, diff)) )
            if int(w/2) > center_inner:
                car.steering_angle = grad
                print(diff, offset, grad)# + (clusters[1][1] - clusters[0][0])))
            else:
                car.steering_angle = 180 - grad
                print(diff, offset, 180 - grad)
        cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)
        cv2.line(cropped_rgb, (0, messsoffset), (w, messsoffset), (0, 0, 255), 3)
        #print('Result',angle.result[1])
        
        if len(clusters) == 2:
            cv2.line(cropped_rgb, (center_inner, 0), (center_inner, h), (0, 255, 255), 3)
        #cv2.line(cropped_rgb, (int(angle.result[1]), 0), (int(angle.result[1]), h), (0, 0, 255), 3)
        cv2.line(cropped_rgb, (int(w/2), 0), (int(w/2), h), (255, 0, 255), 3)
        _, frame_as_jpeg = cv2.imencode(".jpeg", cropped_rgb)

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
            html.P('H'),
            dcc.RangeSlider(id="slider-h", min=0, max=180, value=[80, 114]),
            html.P('S'),
            dcc.RangeSlider(id="slider-s", min=0, max=255, value=[96, 255]),
            html.P('V'),
            dcc.RangeSlider(id="slider-v", min=0, max=255, value=[0,255]),
            html.P('Oben, Unten'),
            dcc.RangeSlider(id="slider-ns", min=0, max=100, value=[35, 85]),
            html.P('Links, Rechts'),
            dcc.RangeSlider(id="slider-we", min=0, max=100),
        ],
        width=6)
    ])
    

])

@app.callback(
    Output("test", "children"),
    Input("slider-h", "value"),
    Input("slider-s", "value"),
    Input("slider-v", "value"),
    Input("slider-ns", "value"),
    Input("slider-we", "value"),
)
def update_p(value_h, value_s, value_v, value_ns, value_we):
    try:
        hsv_range.lower_bound([value_h[0], value_s[0], value_v[0]])
        hsv_range.upper_bound([value_h[1], value_s[1], value_v[1]])
    except:
        pass
    if not value_ns:
        cropp_img.set_ns([0,100])
    else:
        cropp_img.set_ns(value_ns)
    if not value_we:
        cropp_img.set_we([0,100])
    else:
        cropp_img.set_we(value_we)
    #cropp_img.set_ns(value_ns)
    #cropp_img.set_we(value_we)
    #print(cropp_img.ns, cropp_img.we, 1 - cropp_img.ns[1]*0.01)
    return_value = f"Die Einstelungen sind: {value_h}, {value_s}, {value_v}, \n{value_ns}, {value_we}"
    return return_value


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
