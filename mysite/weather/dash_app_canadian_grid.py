# from weather import make_plot
import mysite.weather.common
from . import make_plot, file_download
    # make_plot,
    # group_data,
    # join_provinces,
    # process_raw_df,
    # read_provinces_gjson,
    # read_provinces_geopands,
    # geographic_division_ids,
    # get_data,
    # df_to_gdf,
    # spatial_join_and_group
    # )
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


token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'
px.set_mapbox_access_token(token)


app = DjangoDash('canadian_grid')
# app = dash.Dash(__name__)


print("reading geojson")
# with open('/Users/jpy/Documents/drainage_boundaries_simplifiedpoint2.geojson') as f:
#     drainage_gjson = json.load(f)

with open('/Users/jpy/Documents/canada_grid.geojson') as f:
    grid = json.load(f)
print("finished reading geojsons")
# # read in census data
# drainage_gdf = gpd.read_file('/Users/jpy/Documents/drainage_boundaries.zip')
# # # set crs of census gdf
# drainage_gdf = drainage_gdf.to_crs(pyproj.CRS.from_epsg(4326))
# watershed_gdf = gpd.read_file('/Users/jpy/Documents/NHN_INDEX_WORKUNIT_LIMIT_2')
# watershed_gdf = watershed_gdf.to_crs(pyproj.CRS.from_epsg(4326))
# # assert watersheds_gdf.crs.name == 'WGS 84', f"gdf has crs {watersheds_gdf.crs.name}"
# # if watersheds_gdf.crs.name == 'WGS 84':
# #     print(f"gdf has crs {watersheds_gdf.crs.name}")
#
# data_df = pd.read_csv('/Users/jpy/PycharmProjects/canadian_model/saved_data/canada/2022-02-23_17-17-24.csv')
# data_gdf = df_to_gdf(data_df)
# print("grouping drainage basin data")
# drainage_basin_data_grouped = spatial_join_and_group(data=data_gdf, polygons=drainage_gdf, column_aggregate='DR_Code')
# print("finished grouping drainage basin data")
#
# print("grouping watershed data")
# watershed_data_grouped = spatial_join_and_group(data=data_gdf, polygons=watershed_gdf, column_aggregate='DATASETNAM')
# print("finished watershed basin data")
#
# print("saving drainage basin data")
# drainage_basin_data_grouped.to_csv(f'/Users/jpy/PycharmProjects/canadian_model/saved_data/canada/aggregated/drainage_basins/{datetime.utcnow().strftime("%Y%m%d")}.csv')
# print('done')

# print("saving watershed data")
# watershed_data_grouped.to_csv(f'/Users/jpy/PycharmProjects/canadian_model/saved_data/canada/aggregated/watersheds/{datetime.utcnow().strftime("%Y%m%d")}.csv')
#
# print('done')

print('reading in csv data')

country = 'canada'
df = pd.read_csv(
    f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/{country}/{country}.csv')
print('df to gdf')
gdf = make_plot.df_to_gdf(df)
print('done')

grid_gdf = gpd.read_file('/Users/jpy/Documents/canada_grid.geojson')
gdf.drop('index_right', axis=1, inplace=True)
print('joining grib and grid')
joined = gpd.sjoin(gdf, grid_gdf, how='left')
columns = list(gdf.columns) + ['id']
joined = joined[columns]

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

print('making plot')
@app.callback(
    Output("choropleth", 'figure'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value')
)
def make_choropleth(variable, hour):
    fig = px.choropleth_mapbox(
        joined,
        geojson=grid,
        locations='id',
        featureidkey='properties.id',
        color=f'{variable}_{hour}_binned',
        mapbox_style="satellite-streets",
        opacity=.65,
        zoom=2,
        center={'lat': 60, 'lon': -100},
        height=800,
        width=1000,
        labels=labels,
        hover_data=['longitude', 'latitude', f'{variable}_{hour}'],
        title='Weather Variables Visualized Over 0.15 Degree Resolution'

    )

    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        autosize=True,
    )
    # if variable != 't2m':
    #     fig.update_coloraxes(
    #         # cmin=1,
    #         # cmax=joined[f'{variable}_{hour}'].max(),
    #         colorscale=[
    #              [0, 'rgba(13, 8, 135, 0)'],
    #              [.0001, 'rgba(13, 8, 135, .6)'],
    #              [.5, '#d8576b'],
    #              [1, "#f0f921"]]
    #     )
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
        # debug=True,
        host='127.0.0.1',
        port=8055,
        use_reloader=False,
        dev_tools_ui=True,
        dev_tools_prune_errors=True
    )