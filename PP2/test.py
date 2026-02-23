from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, Response
from basisklassen_cam.py 

external_stylessheets = [dbc.themes.DARKLY]
server = Flask

cam = Camera()
app = Dash(external_stylesheets=external_stylessheets, server=server)

@server.route("/test")

def genreate_stream(cam):
        while True:
                frame = cam.get_frame()


app.layout = html.Div([
    html.H1("Hallo Projektphase"),
    html.P("Test", id="test"),
    dcc.RangeSlider(id="slider-h", min=0, max=180)
])

@app.callback(
    Output("test", "children"),
    Input("slider-h", "value")
)

def update_p(value_h, value_s, value_v):
        return_value = f"Die Einstellung sind: {value_h}, {value_s}, {value_v}"
        return return_value

if __name__== "__main__":
        app.run(host="0.0.0.0", debug=True)
