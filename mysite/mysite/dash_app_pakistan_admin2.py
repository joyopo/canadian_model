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

# aggregate data on keyword

data_grouped = spatial_join_and_group(gdf, pakistan_gdf, 'ADM2_PCODE')

# data_grouped = joined_df.dropna()
# data_grouped = joined_df.groupby('ADM2_PCODE')[['t2m', 'prate', 'si10', 'sde']].agg(['mean'])
# data_grouped.reset_index(inplace=True, drop=False)
# data_grouped.columns = ["_".join(a) for a in data_grouped.columns.to_flat_index()]


# join aggregated data with locations
# last_join_gdf = pd.merge(left=pakistan_gdf, right=data_grouped, how='right')
# last_geojson = json.loads(last_join_gdf.to_json())

print('done with data')
print('computing layout')

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
def make_choropleth(variable, hour):
    fig = px.choropleth_mapbox(
        data_grouped,
        geojson=pakistan_gjson,
        locations="ADM2_PCODE",
        featureidkey='properties.ADM2_PCODE',
        color=f'{variable}_{hour}',
        mapbox_style="satellite-streets",
        opacity=.6,
        zoom=4,
        center={'lat': 30, 'lon': 68},
        height=800,
        width=800,
        labels={ # value: label,
                'ADM2_PCODE_': 'Administrative Boundary Code'},
        title='Weather variables aggregated over Administrative District boundaries'
           )

    return fig




# ----------- using go.Figure() --------------
# @app.callback(
#     Output("choropleth", 'figure'),
#     Input('weather-dropdown', 'value')
# )
# def display_map(value):
#     fig = go.Figure(data=go.Choroplethmapbox(
#         geojson=pakistan_gjson,
#         locations=data_grouped['ADM2_PCODE_'],  # Spatial coordinates
#         z=data_grouped[value],  # Data to be color-coded
#         featureidkey='properties.ADM2_PCODE',
#         # mapbox_style="open-street-map",
#         # locationmode = 'USA-states', # set of locations match entries in `locations`
#         # colorscale = 'Reds',
#         # colorbar_title = "Millions USD",
#     ))
#
#     fig.update_layout(mapbox_style='open-street-map',
#                       # center={'lat': 30, 'lon': 68},
#                       )
#
#     return fig


print("finished making plot")
print("computing layout")
# app.layout = html.Div([
#     html.P("Poop:"),
#     # dcc.RadioItems(
#     #     id='candidate',
#     #     options=[{'value': x, 'label': x}
#     #              for x in candidates],
#     #     value=candidates[0],
#     #     labelStyle={'display': 'inline-block'}
#     # ),
#     dcc.Graph(figure=fig)
# ])
if __name__ == '__main__':
    app.run_server(
        # debug=True)
        host='127.0.0.1',
        port='7080',
        use_reloader=False,
        dev_tools_ui=True,
        dev_tools_prune_errors=True
    )
