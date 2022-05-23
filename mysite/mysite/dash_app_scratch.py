from mysite.weather.make_plot import (
    make_plot,
    group_data,
    join_provinces,
    process_raw_df,
    read_provinces_gjson,
    read_provinces_geopands,
    # read_process_temp,
    geographic_division_ids,
    get_data,
    df_to_gdf
    )
from mysite.weather.file_download import full_download
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import geopandas as gpd
import geojson
import json
from urllib.request import urlopen

from django_plotly_dash import DjangoDash
import plotly.express as px
import plotly.graph_objects as go
# from dash_app_code import token
token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

px.set_mapbox_access_token(token)

# ------------- Choropleth with Montreal Dataset -----------------

# df = px.data.election()
# geojson = px.data.election_geojson()
# candidates = df.winner.unique()
#
# print("finished fetching data")
# print(candidates)
#
# app = dash.Dash(__name__)
#
# print("computing layout")
# app.layout = html.Div([
#     html.P("Candidate:"),
#     dcc.RadioItems(
#         id='candidate',
#         options=[{'value': x, 'label': x}
#                  for x in candidates],
#         value=candidates[0],
#         labelStyle={'display': 'inline-block'}
#     ),
#     dcc.Graph(id="choropleth"),
# ])
#
# print("building plot")
# @app.callback(
#     Output("choropleth", "figure"),
#     [Input("candidate", "value")])
# def display_choropleth(candidate):
#     fig = px.choropleth_mapbox(
#         df, geojson=geojson, color=candidate,
#         locations="district", featureidkey="properties.district",
#         center={"lat": 45.5517, "lon": -73.7073}, zoom=9,
#         range_color=[0, 6500])
#     fig.update_layout(
#         margin={"r":0,"t":0,"l":0,"b":0},
#         mapbox_accesstoken=token)
#
#     return fig


# -------------- Scatter with Canadian Data ----------------
print("starting!")

country = 'canada'

df = pd.read_csv(
    f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/{country}/{country}.csv'
)


# df.loc[df['prate'] == 0, ['prate_bin']] = '0'
# df.loc[df['prate'].between(0, .0005, inclusive='neither'), ['prate_bin']] = '0-.0005'
# df.loc[df['prate'].between(.0005, .001, inclusive='both'), ['prate_bin']] = '.0005-.001'
# df.loc[df['prate'].between(.001, .0015, inclusive='neither'), ['prate_bin']] = '.001-.0015'
# df.loc[df['prate'].between(.0015, .002, inclusive='both'), ['prate_bin']] = '.0015-.002'
# df.loc[df['prate'].between(.002, .0025, inclusive='neither'), ['prate_bin']] = '.002-.0025'
# df.loc[df['prate'] > .0025, ['prate_bin']] = '> .0025'




gdf = df_to_gdf(df)
print("got the data")

app = dash.Dash(__name__)

# fig = go.Figure()

# fig.update_layout(
#     mapbox_style="open-street-map"
# )

print("doing the layout")
app.layout = html.Div([
    html.H1("Pakistan Weather Portal"),
    html.Div([
        html.P('choose a weather variable from the dropdown below to overlay on the map')
    ]),
    dcc.Dropdown(
        options=[
            {'label': 'Surface Temperature (kelvin)', 'value': 't2m'},
            {'label': 'Wind Speed (meters/second)', 'value': 'si10'},
            {'label': 'Snow Depth (meters)', 'value': 'sde'},
            {'label': 'Surface Precipitation Rate (kg m-2 sec-1)', 'value': 'prate'}
        ],
        value='t2m',
        id='weather-dropdown',
        placeholder='Select a Weather Variable'
    ),

    # html.Div(id='wd-output-container'),
    dcc.Graph(id='choropleth'),

    dcc.Slider(
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
    ),

])

print('making plot')
@app.callback(
    Output("choropleth", 'figure'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value')
)
def display_scatter_map(variable, hour):
    # if value == 'prate':
    #     gdf = gdf.loc[gdf['prate'] > 0]

    fig = px.scatter_mapbox(
        gdf,
        lat=gdf.geometry.y,
        lon=gdf.geometry.x,
        zoom=2,
        center={'lat': 60, 'lon': -100},
        # hover_data=[value],
        color=f'{variable}_{hour}',
        # color_discrete_sequence=px.colors.sequential.Plasma_r,
        opacity=.4,
        height=800,
        width=800,
        mapbox_style='satellite-streets',
        title='Weather variables plotted at 15km resolution'
    )

    return fig

# 'https://data.opendatasoft.com/explore/dataset/georef-canada-province@public/download/?format=geojson&timezone=America/New_York&lang=en'
# def read_provinces_gjson(url):
#     with urlopen(url) as response:
#         provinces_gjson = json.load(response)
#
#     return provinces_gjson

# provinces = read_provinces_gjson('https://data.opendatasoft.com/explore/dataset/georef-canada-province@public/download/?format=geojson&timezone=America/New_York&lang=en')

# fig.update_layout(
#     mapbox_layers=[
#         {
#             "sourcetype": 'geojson',
#             'source': provinces
#         }
#     ]
# )
print('making it look pretty')


if __name__ == '__main__':
    app.run_server(
        host='127.0.0.1',
        port=8000,
        use_reloader=False,
        dev_tools_ui=True,
        dev_tools_prune_errors=True
    )
