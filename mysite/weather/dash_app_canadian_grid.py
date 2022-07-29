from .common import generate_plot_labels, generate_slider_marks, grid_layout, update_datatable_grid, \
    filter_and_download_grid
# from mysite.weather.common import generate_plot_labels, generate_slider_marks, generate_radio_options, \
#     display_click_grid_data_in_datatable, filter_and_download_grid, grid_layout, update_datatable_grid

from . import file_download
# import mysite.weather.file_download as file_download


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import geopandas as gpd
import geojson
import json
import pyproj

from django_plotly_dash import DjangoDash
import plotly.express as px
import datetime

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
gdf = file_download.df_to_gdf(df)
print('done')

grid_gdf = gpd.read_file('/Users/jpy/Documents/canada_grid.geojson')
gdf.drop('index_right', axis=1, inplace=True)
print('joining grib and grid')
joined = gpd.sjoin(gdf, grid_gdf, how='left')
columns = list(gdf.columns) + ['id']
joined = joined[columns]

print('making labels')
labels = generate_plot_labels()
slider_marks, dummy_code_hours = generate_slider_marks()

# define start time
start_time = df['valid_time_0'][0]
try:
    start_time_label = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
except:
    start_time_date = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    start_time_label = datetime.datetime.combine(start_time_date, datetime.datetime.min.time())


# start_time = f"{df['valid_time_0'][0]} UTC"
# if ':' not in start_time:
#     start_time = start_time.replace('UTC', '00:00 UTC')


print("computing layout")
grid_layout = grid_layout(slider_marks, start_time_label)

app.layout = grid_layout


@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('choropleth', 'clickData'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value'),
    State('data-table', 'data')
)
def update_grid_datatable(clickdata, variable, hour, existing_data, **kwargs):
    if clickdata is not None:
        data_table_columns, data = update_datatable_grid(
            clickdata=clickdata,
            variable=variable,
            hour=hour,
            existing_data=existing_data,
            df=joined,
            dummy_code_hours=dummy_code_hours,
            start_time=start_time_label,
            **kwargs
        )

    return data_table_columns, data


@app.callback(
    Output('download', 'data'),
    Input('btn', 'n_clicks'),
    State('data-table', 'data'),
    State('weather-dropdown', 'value'),
)
def filter_and_download(n_clicks, data, variable):
    if n_clicks is not None:
        download_df = filter_and_download_grid(
            data=data,
            variable=variable,
            df=joined,
            start_time=start_time_label
        )

    return dcc.send_data_frame(download_df.to_csv, f'{country}_weather_portal.csv')


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
        color=f'{variable}_{dummy_code_hours[hour]}',
        mapbox_style="satellite-streets",
        opacity=.65,
        zoom=2,
        center={'lat': 60, 'lon': -100},
        height=800,
        # width=1000,
        labels=labels,
        hover_data=['longitude', 'latitude', f'{variable}_{dummy_code_hours[hour]}'],
        title='Canada Grid',
        custom_data=['latitude', 'longitude', f'{variable}_{dummy_code_hours[hour]}']

    )

    fig.update_traces(
        marker_line_width=0,
    )
    fig.update_layout(
        autosize=True,
        margin=dict(
            l=10,
            r=10,
            b=10,
            t=10,
        )
    )

    fig.update_coloraxes(
        colorbar_orientation='h',
        colorbar_title_side='top'
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
        debug=True,
        # host='127.0.0.1',
        # port=8055,
        # use_reloader=False,
        # dev_tools_ui=True,
        # dev_tools_prune_errors=True
    )
