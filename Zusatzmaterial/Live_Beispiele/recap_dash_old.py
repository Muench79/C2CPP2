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

os.system('sudo iw dev wlan0 set power_save off')
car = BaseCar()
car.steering_angle = 90
car.drive2(0)
#sys.exit()

class SteeringAngle:
    def __init__(self):
        self.__line_inner_1 = ()
        self.__line_inner_2 = ()
        self.__line_outer_1 = ()
        self.__line_outer_2 = ()
        self.__offset = 0
        self.__screen_center = 0

    def screen_center(self, c):
        self.__screen_center = c

    def line_inner_1(self, x1, y1, x2, y2):
        self.__line_inner_1 = (x1, y1, x2, y2)
        #print(self.__line_inner_1)
    
    def line_inner_2(self, x1, y1, x2, y2):
        self.__line_inner_2 = (x1, y1, x2, y2)
        #print(self.__line_inner_2)

    def line_outer_1(self, x1, y1, x2, y2):
        self.__line_outer_1 = (x1, y1, x2, y2)
        #print(self.__line_outer_1)
    
    def line_outer_2(self, x1, y1, x2, y2):
        self.__line_outer_2 = (x1, y1, x2, y2)

    def measuring_offset(self, offset):
        self.__offset = offset
        #print(self.__line_outer_2)
    
    def __str__(self):
        return ('Inner_1: ' + str(self.__line_inner_1) + '\n'
                'Inner_2: ' + str(self.__line_inner_2) + '\n'
                'Outer_1: ' + str(self.__line_outer_1) + '\n'
                'Outer_1: ' + str(self.__line_outer_2) + '\n'
                'Angle: ' + str(self.result) + '\n'
                'Center: ' + str(self.__screen_center) + '\n'
                'Offset: ' + str(self.__offset))
    #x=((100-y1)*(x2-x1)/(y2-y1))+x1
    
    
    def __diff(self, x1, y1, x2, y2):
        return ((self.__offset - y1) * (x2-x1) / (y2-y1)) + x1
    
    @property
    def result(self):
        center = self.__screen_center
        offset = self.__offset
        try:
            
            
            x_i_1 = self.__diff(*self.__line_inner_1)
            x_i_2 = self.__diff(*self.__line_inner_2)
            x_o_1 = self.__diff(*self.__line_outer_1)
            x_o_2 = self.__diff(*self.__line_outer_2)

            m_1 = (x_i_2 - x_i_1) / 2 + x_i_1
            m_2 = (x_o_2 - x_o_1) / 2 + x_o_1

            m_mean = (m_1 + m_2) / 2
        except:
            return 90, 0
        
        angle = math.degrees(math.atan2(offset, (center - m_mean)))
        
        return  (angle, m_mean)
    
berechnung = SteeringAngle()
berechnung.measuring_offset(50)
berechnung.line_inner_1(52, 113, 105, 56)
berechnung.line_inner_2(285, 63, 302, 118)
berechnung.line_outer_1(29, 106, 86, 50)
berechnung.line_outer_2(300, 61, 319, 111)
berechnung.screen_center(160)
print("Ergebnis\n",berechnung.result)

angle = SteeringAngle()

class HSVRange:
    def __init__(self, lb, ub):
        self.lb = np.array(lb)
        self.ub = np.array(ub)
    #hsv_range.lower_bound([value_h[0], value_s[0], value_v[0]])
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
    @property
    def h_min_max(self):
        return self.lb[0, 0],self.lb[0, 1] 

hsv_range = HSVRange([80,96,0], [114,255,255])
print(hsv_range.lb[0])
#sys.exit()
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


try:
    with open('config.json', 'r') as f:
        data = json.load(f)
        turning_offset = data['turning_offset']
        forward_A = data['forward_A']
        forward_B = data['forward_B']

except Exception as e:
    hsv_range = HSVRange([80,96,0], [114,255,255])
    cropp_img = Cropp()



external_stylesheets = [dbc.themes.DARKLY]
server = Flask(__name__)





    


#sys.exit()
def winkel(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    theta = math.atan2(dy, dx)          # Winkel in Radiant
    grad = math.degrees(theta)          # Umrechnung in Grad
    return grad



cam = Camera()

app = Dash(external_stylesheets=external_stylesheets, server=server)

@server.route("/test")
def unterseite_test():
    return "Hier ist die zweite Seite"




def generate_stream(cam):
    while True:

        #car.drive2(20)
        linien_rechts = []
        linien_links = []
        linien_rechts_sortiert = []
        linien_links_sortiert = []
        
        frame = cam.get_frame()
        resized = cv2.resize(frame, None, fx=0.5, fy=0.5)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        
        filtered = cv2.inRange(hsv, hsv_range.lowerbound, hsv_range.upperbound)
        #filtered = cv2.inRange(hsv, np.array([90, 0, 0]), np.array([120, 255, 255]))
        h, w = filtered.shape
<<<<<<< HEAD
=======
        
        #print(filtered.shape)
        #print('jhjjhhdjfhguhr', cropp_img.ns[0]*0.1)
        #print("Was kommt hier raus?", cropp_img.ns)
>>>>>>> joema
        int(h - (cropp_img.ns[1] * 0.01 * h))
        #resized = resized[int(cropp_img.ns[0]*0.01*h):int(h - (cropp_img.ns[1] * 0.01 * h)), :]
        resized = resized[int(cropp_img.ns[0]*0.01*h):int(cropp_img.ns[1]*0.01*h), int(cropp_img.we[0]*0.01*w):int(cropp_img.we[1]*0.01*w):]
        messsoffset = resized.shape[0] - 50
        

        #cropped = filtered[int(cropp_img.ns[0]*0.01*h):int(h - (cropp_img.ns[1] * 0.01 * h)):, :]
        cropped = filtered[int(cropp_img.ns[0]*0.01*h):int(cropp_img.ns[1]*0.01*h), int(cropp_img.we[0]*0.01*w):int(cropp_img.we[1]*0.01*w):]
        
        h, w, c = resized.shape
        angle.screen_center(int(w/2))
        angle.measuring_offset(50)
        median_blurred = cv2.medianBlur(cropped, 13)
        edges = cv2.Canny(median_blurred, 100, 200)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=20, minLineLength=20, maxLineGap=10)
        
        #cv2.line(resized, (10, 0), (100, 100), (0, 255, 0), 2)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x1 > int(w/2):

                    if y2 < y1:
                        if y2 <= messsoffset <= y1:
                            linien_rechts.append((x1, y1, x2, y2))
                    else:
                        if y1 <= messsoffset <= y2:
                            linien_rechts.append((x1, y1, x2, y2))
                    linien_rechts_sortiert = sorted(linien_rechts, key=lambda v: v[0])
                    cv2.line(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)
                else:
                    if y2 < y1:
                        if y2 <= messsoffset <= y1:
                            linien_links.append((x1, y1, x2, y2))
                    else:
                        if y1 <= messsoffset <= y2:
                            linien_links.append((x1, y1, x2, y2))
                    linien_links_sortiert = sorted(linien_links, key=lambda v: v[0])
                    cv2.line(resized, (x1, y1), (x2, y2), (0, 255, 255), 2)
                #print(int(winkel(x1,y1,x2,y2)))
                #print(winkel(1,1,1,10))
            if len(linien_rechts_sortiert) > 1 and len(linien_links_sortiert) > 1:
                angle.line_inner_1(*linien_links[-1])
                angle.line_inner_2(*linien_rechts[0])
                angle.line_outer_1(*linien_links[0])
                angle.line_outer_2(*linien_rechts[-1])
                car.steering_angle = angle.result[0]
        
        cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)
        cv2.line(cropped_rgb, (0, messsoffset), (w, messsoffset), (0, 0, 255), 3)
        #print('Result',angle.result[1])
        cv2.line(cropped_rgb, (int(angle.result[1]), 0), (int(angle.result[1]), h), (0, 0, 255), 3)
        cv2.line(cropped_rgb, (int(w/2), 0), (int(w/2), h), (255, 0, 255), 3)
        _, frame_as_jpeg = cv2.imencode(".jpeg", cropped_rgb)

        frame_in_bytes = frame_as_jpeg.tobytes()

        frame_as_string = (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_in_bytes + b'\r\n\r\n')
#sys.exit()
        #print('Links', messsoffset, int(w/2), angle.result, '#'*40)
        print(angle)
        #pprint.pprint(linien_links_sortiert)
        #print('Rechts' + '#'*40)
        #pprint.pprint(linien_rechts_sortiert)
        x_links_a = messsoffset
        x_links_i = messsoffset
        x_rechts_a = messsoffset
        #x_rechts_i = 
        #x=((100-y1)*(x2-x1)/(y2-y1))+x1
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
            dcc.RangeSlider(id="slider-h", min=0, max=180, value= [hsv_range.lb[0].item(), hsv_range.ub[0].item()]),
            html.P('S'),
            dcc.RangeSlider(id="slider-s", min=0, max=255, value=[96, 255]),
            html.P('V'),
            dcc.RangeSlider(id="slider-v", min=0, max=255, value=[0,255]),
            html.P('Oben, Unten'),
            dcc.RangeSlider(id="slider-ns", min=0, max=100, value=[35, 85]),
            html.P('Links, Rechts'),
            dcc.RangeSlider(id="slider-we", min=0, max=100),
            html.P('Geschwindigkeit'),
            dcc.Slider(id="slider-speed", min=0, max=30, value=0),
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
    Input("slider-speed", "value"),
)
def update_p(value_h, value_s, value_v, value_ns, value_we, value_speed):
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
    print(value_speed)
    car.drive2(int(value_speed))
    #cropp_img.set_ns(value_ns)
    #cropp_img.set_we(value_we)
    #print(cropp_img.ns, cropp_img.we, 1 - cropp_img.ns[1]*0.01)
    return_value = f"Die Einstellungen sind: {value_h}, {value_s}, {value_v}, \n{value_ns}, {value_we}"
    return return_value


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
