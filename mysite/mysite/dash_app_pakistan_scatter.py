from mysite.weather.make_plot import (
    make_plot,
    group_data,
    join_provinces,
    process_raw_df,
    read_provinces_gjson,
    read_provinces_geopands,
    geographic_division_ids,
    get_data,
    df_to_gdf,
    spatial_join_and_group
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

app = dash.Dash(__name__)

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

px.set_mapbox_access_token(token)

with open('/Users/jpy/Documents/pakistan.geojson') as f:
    pakistan_gjson = json.load(f)
# nb_gjson = read_provinces_gjson('https://gnb.socrata.com/api/geospatial/js6t-a99d?method=export&format=GeoJSON')
pakistan_gdf = gpd.read_file('/Users/jpy/Downloads/pak_adm_ocha_pco_gaul_20181218_SHP/admin2')
# pakistan_json = pakistan_gdf.to_json()
# pakistan_gjson = json.loads(pakistan_json)
print('done reading gjson')
print('reading live data')
country = 'pakistan'
df = pd.read_csv(
    f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/{country}/{country}.csv')
gdf = df_to_gdf(df)

print("joining gdfs")
# joined_df = gpd.sjoin(pakistan_gdf, gdf, how='left')

# bounded scatter
pakistan_border = gpd.read_file('/Users/jpy/Downloads/pak_adm_ocha_pco_gaul_20181218_SHP/admin0')
bounded_scatter = gpd.sjoin(pakistan_border, gdf, how='left')
bounded_scatter = bounded_scatter[df.columns]
bounded_scatter = bounded_scatter.drop('geometry', axis=1)

gdf = df_to_gdf(bounded_scatter)

# aggregate data on keyword

# data_grouped = spatial_join_and_group(gdf, pakistan_gdf, 'ADM2_PCODE')


print('done with data')
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
        zoom=4,
        center={'lat': 30, 'lon': 68},
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


if __name__ == '__main__':
    app.run_server(
        debug=True)
    #     host='127.0.0.1',
    #     port='7080',
    #     use_reloader=False,
    #     dev_tools_ui=True,
    #     dev_tools_prune_errors=True
    # )
