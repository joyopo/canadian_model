from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import geopandas as gpd
import geojson
import json
import pyproj

from django_plotly_dash import DjangoDash
import plotly.express as px
from datetime import datetime


app = Dash(__name__)
app.layout = html.Div([
    html.Button("Download Netcdf", id="btn_netcdf"),
    dcc.Download(id="download-netcdf")
])


@app.callback(
    Output("download-netcdf", "data"),
    Input("btn_netcdf", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_file(
        path='/Users/jpy/PycharmProjects/canadian_model/mysite/mysite/precip.mon.mean.nc',

    )


if __name__ == "__main__":
    app.run_server(
        host='127.0.0.1',
        port=8060,
        use_reloader=False,
        dev_tools_ui=True,
        dev_tools_prune_errors=True
    )