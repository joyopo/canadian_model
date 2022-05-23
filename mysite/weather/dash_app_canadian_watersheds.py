# from mysite.weather.make_plot import (
#     make_plot,
#     group_data,
#     join_provinces,
#     process_raw_df,
#     read_provinces_gjson,
#     read_provinces_geopands,
#     geographic_division_ids,
#     get_data,
#     df_to_gdf,
#     spatial_join_and_group
#     )
import dash
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

import mysite.weather.common
from . import file_download



token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'
px.set_mapbox_access_token(token)


app = DjangoDash('canadian_watersheds')
# app = dash.Dash(__name__)


print("reading geojson")
# with open('/Users/jpy/Documents/drainage_boundaries_simplifiedpoint2.geojson') as f:
#     drainage_gjson = json.load(f)

with open('/Users/jpy/Documents/weather_portal/final_watershed_geojsons/canada_watersheds_level6_simplified_0.005.geojson') as f:
    watersheds = json.load(f)
print("finished reading geojsons")


print('reading in csv data')

watershed_data_grouped = pd.read_csv(f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/canada/aggregated/watersheds/watersheds.csv')

print('making labels')
labels = mysite.weather.common.generate_plot_labels()


print("computing layout")
app.layout = html.Div([
    # html.H1("Pakistan Weather Portal"),
    # html.Div([
    #     html.P('choose a weather variable from the dropdown below to overlay on the map')
    # ]),
    html.Div([dcc.Dropdown(
        options=[
            {'label': 'Surface Temperature (celsius)', 'value': 't2m'},
            {'label': 'Wind Speed (meters/second)', 'value': 'si10'},
            {'label': 'Snow Depth (meters)', 'value': 'sde'},
            {'label': 'Surface Precipitation Rate (kg m-2 sec-1)', 'value': 'prate'}
        ],
        value='t2m',
        id='weather-dropdown',
        placeholder='Select a Weather Variable'
    )], style={'marginBottom': 20}),

    html.Div([dcc.Slider(
        min=0,
        max=240,
        step=None,
        marks={
            0: '0 hours',
            120: '120 hours',
            240: '240 hours',
        },
        value=0,

        id='hour-slider'
    )], style={
        'border': '1px grey solid',
        'padding': 10,
        'marginBottom': 20
        # 'marginTop': 10
    }),

    html.Div([dcc.Graph(id='choropleth')])]
)
print('finished computing layout')
print('building plot')

@app.callback(
    Output("choropleth", 'figure'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value')
)
def make_choropleth(variable, hour):
    fig = px.choropleth_mapbox(
        watershed_data_grouped,
        geojson=watersheds,
        locations=watershed_data_grouped['HYBAS_ID'],
        featureidkey='properties.HYBAS_ID',
        color=f'{variable}_{hour}',
        mapbox_style="satellite-streets",
        opacity=.65,
        zoom=2,
        center={'lat': 60, 'lon': -100},
        height=800,
        width=1000,
        labels=labels,
        hover_data=['HYBAS_ID', f'{variable}_{hour}'],
        title='Weather variables aggregated over level 6 Pfafstetter watershed boundaries'

    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=.5
    )

    fig.update_layout(
        autosize=True,
    )

    return fig

#     make_plot(
#     df=gdf_merged,
#     geojson=gdf_merged.geometry,
#     # featureidkey=gdf["CSDUID"],
#     # f"properties.{geographic_division_ids['census_subdivision']}",
#     locations=gdf_merged.index,
# )
print("finished building plot")

# fig.update_layout(
#     margin={"r": 0, "t": 0, "l": 0, "b": 0},
#     mapbox_accesstoken=token)


if __name__ == '__main__':
    app.run_server(
        host='127.0.0.1',
        port=8050,
        debug=True
        # use_reloader=False,
        # dev_tools_ui=True,
        # dev_tools_prune_errors=True
    )