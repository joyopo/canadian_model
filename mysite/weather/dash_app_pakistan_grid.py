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
# from mysite.weather import file_download
from . import file_download


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash import dash_table

from dash.dependencies import Input, Output, State
# from dash_extensions import Download
# from dash_extensions.snippets import send_data_frame
import pandas as pd
import geopandas as gpd
import geojson
import json
from urllib.request import urlopen
from django_plotly_dash import DjangoDash
import plotly.express as px
import plotly.graph_objects as go
# from dash_app_code import token
from django_plotly_dash import DjangoDash
from .common import generate_plot_labels, generate_slider_marks, generate_radio_options
# from mysite.weather.common import generate_plot_labels, generate_slider_marks, generate_radio_options

# app = dash.Dash(__name__)
app = DjangoDash('pakistan_grid')

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

px.set_mapbox_access_token(token)

# creating hover labels


with open('/Users/jpy/Documents/pakistan_grid.geojson') as f:
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
gdf = file_download.df_to_gdf(df)

# joining grid shapes and data
grid_gdf = gpd.read_file(f'/Users/jpy/Documents/{country}_grid.geojson')
# gdf.drop('index_right', axis=1, inplace=True)
joined = gpd.sjoin(gdf, grid_gdf, how='left')
columns = list(gdf.columns) + ['id']
joined = joined[columns]

print("joining gdfs")
# joined_df = gpd.sjoin(pakistan_gdf, gdf, how='left')

# bounded scatter

# aggregate data on keyword


# data_grouped = joined_df.dropna()
# data_grouped = joined_df.groupby('ADM2_PCODE')[['t2m', 'prate', 'si10', 'sde']].agg(['mean'])
# data_grouped.reset_index(inplace=True, drop=False)
# data_grouped.columns = ["_".join(a) for a in data_grouped.columns.to_flat_index()]


# join aggregated data with locations
# last_join_gdf = pd.merge(left=pakistan_gdf, right=data_grouped, how='right')
# last_geojson = json.loads(last_join_gdf.to_json())

print('done with data')
print('making labels')
labels = generate_plot_labels()
radio_options = generate_radio_options()
slider_marks, dummy_code_hours = generate_slider_marks()
print('computing layout')



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
        step=1,
        marks=slider_marks,
        value=0,
        id='hour-slider'
    )], style={
        'border': '1px grey solid',
        'padding': 10,
        'marginBottom': 20}),

    # html.Table([
    #     html.Tr([html.Td(['Latitude']), html.Td(id='lat')]),
    #     html.Tr([html.Td(['Longitude']), html.Td(id='lon')]),
    #     html.Tr([html.Td(['Value']), html.Td(id='val')]),
    #
    # ]),

    # html.Pre(id='click-data'),
    dash_table.DataTable(
        id='data-table',
    ),

    html.Button("Download", id="btn"),
    dcc.Download(id="download"),
    dcc.Store(id='memory'),

    html.Div([dcc.Graph(id='choropleth')])  # style={'display': 'inline-block'}

    ]
)

print('making plot')


@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('choropleth', 'clickData'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value')
)
def display_click_data(clickdata, variable, hour):
    json_string = json.dumps(clickdata)
    data = json.loads(json_string)
    location = data['points'][0]['location']
    latitude = data['points'][0]['customdata'][0]
    longitude = data['points'][0]['customdata'][1]
    value = joined.loc[(joined.id == location), f'{variable}_{dummy_code_hours[hour]}'].item()
    # data['points'][0]['customdata'][2]
    # 'id' is the row id
    data = [
        {
            'location_id': location,
            'latitude': latitude,
            'longitude': longitude,
            f'{variable}_{dummy_code_hours[hour]}': value,
            'id': 0}
    ]
    data_table_columns = [{
        'name': 'latitude',
        'id': 'latitude'
    }, {
        'name': 'longitude',
        'id': 'longitude'
    }, {
        'name': 'location_id',
        'id': 'location_id'
    }, {
        'name': f'{variable}_{dummy_code_hours[hour]}',
        'id': f'{variable}_{dummy_code_hours[hour]}'
    }]

    return data_table_columns, data
    # return json.dumps(clickData)


@app.callback(
    Output('download', 'data'),
    Input('btn', 'n_clicks'),
    State('data-table', 'data'),
    State('weather-dropdown', 'value'),
)
def filter_and_download(n_clicks, data, variable):
    lat = data[0]['latitude']
    lon = data[0]['longitude']
    # function to get coordinates of square around click point here

    lat_lon_list = []
    lat_lon_list.append([lat, lon])

    lat_lon_list.append([lat + .15, lon])
    lat_lon_list.append([lat - .15, lon])
    lat_lon_list.append([lat, lon + .15])
    lat_lon_list.append([lat, lon - .15])

    lat_lon_list.append([lat + .15, lon + .15])
    lat_lon_list.append([lat - .15, lon - .15])
    lat_lon_list.append([lat + .15, lon - .15])
    lat_lon_list.append([lat - .15, lon + .15])

    download_df = pd.DataFrame(data={}, columns=joined.columns)
    for i in lat_lon_list:
        filtered_row = joined.loc[(joined['latitude'] == i[0]) & (joined['longitude'] == i[1])]
        download_df = download_df.append(filtered_row)

    # filter download_df to just the variable selected
    cols_to_keep = ['latitude', 'longitude', 'id', 'valid_time_0']
    for col in download_df.columns:
        if col.startswith(variable) and not col.endswith('binned'):
            cols_to_keep.append(col)

    download_df = download_df[cols_to_keep]

    # add 'hours' to end of forecast columns
    for col in download_df.columns:
        if col.startswith(variable):
            download_df = download_df.rename(columns={col: col + '_hours'})
    download_df = download_df.rename(columns={'valid_time_0': 'forecast_start_time'})

    # columns_to_transpose = []
    # for col in download_df_f:
    #     if col.startswith('t2m'):
    #         columns_to_transpose.append(col)
    # df_to_transpose = download_df_f[columns_to_transpose]
    # download_df_f = download_df_f.drop(columns_to_transpose)

    # return download_df.to_dict()
    return dcc.send_data_frame(download_df.to_csv, f'{country}_weather_portal.csv')



# @app.callback(
#     Output('download', 'data'),
#     Input('memory', 'data'),
#     Input('btn', 'n_clicks')
# )
# def download_data(data, n_clicks):
#     download_df = pd.DataFrame(data)
#     return dcc.send_data_frame(download_df.to_csv, f'{country}_weather_portal.csv')


@app.callback(
    Output("choropleth", 'figure'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value')
)
def make_choropleth(variable, hour):
    fig = px.choropleth_mapbox(
        joined,
        geojson=pakistan_gjson,
        locations='id',
        featureidkey='properties.id',
        color=f'{variable}_{dummy_code_hours[hour]}',
        mapbox_style="satellite-streets",
        opacity=.6,
        zoom=4,
        center={'lat': 30, 'lon': 68},
        height=800,
        width=1000,
        labels=labels,  # .update({'ADM2_PCODE_': 'Administrative Boundary Code'}),
        hover_data=['longitude', 'latitude', f'{variable}_{dummy_code_hours[hour]}'],
        title='Weather Variables Visualized Over 0.15 Degree Resolution',
        custom_data=['latitude', 'longitude', f'{variable}_{dummy_code_hours[hour]}']
    )

    fig.update_traces(
        # overwrite=True,
        marker_line_width=0,
        autocolorscale=False,
        # colorscale=[[0, 'blue'], [.5, 'green'], [1, 'red']]
    )
    fig.update_layout(
        autosize=True,
        # sliders=[{'len': 800}, {'lenmode': 'pixels'}]
    )

    # test
    # if

    if variable != 't2m':
        fig.update_coloraxes(cmin=1, cmax=joined[f'{variable}_{dummy_code_hours[hour]}'].max(),
                             colorscale=[
                                 [0, 'rgba(13, 8, 135, .6)'],
                                 # [.0001, 'rgba(13, 8, 135, .6)'],
                                 #     [.01, f'rgba(23.846153846153847, 178.15384615384616, 221.53846153846155, 0)'],
                                 #     [.1, f'rgba(42.69230769230769, 163.30769230769232, 203.0769230769231, 0)'],
                                 #     [.2, f'rgba(61.53846153846154, 148.46153846153845, 184.6153846153846, {opacity})'],
                                 #     [.3, f'rgba(80.38461538461539, 133.6153846153846, 166.15384615384616, {opacity})'],
                                 #     [.4, f'rgba(99.23076923076923, 118.76923076923077, 147.6923076923077, {opacity})'],
                                 [.5, '#d8576b'],
                                 #     [.6, f'rgba(136.92307692307693, 89.07692307692307, 110.76923076923077, {opacity})'],
                                 #     [.7, f'rgba(155.76923076923077, 74.23076923076923, 92.30769230769232, {opacity})'],
                                 #     [.8, f'rgba(174.6153846153846, 59.38461538461539, 73.84615384615387, {opacity})'],
                                 #     [.9, f'rgba(193.46153846153845, 44.53846153846155, 55.384615384615415, {opacity})'],
                                 #     # ['rgba(212.30769230769232, 29.69230769230768, 36.923076923076934, .6)'],
                                 #     # ['rgba(231.15384615384616, 14.84615384615384, 18.46153846153848, .6)'],
                                 [1, "#f0f921"]]
                             )
    else:
        pass

        # fig.update_coloraxes(
        #         colorscale=COLORSCALES[variable]
        #     )
        # else:

        # [[0, 'rgba(5, 193, 240, .6)'], [1, 'rgba(250, 0, 0, .6)']])

    return fig


#     COLORSCALES = {
#     't2m': [
#             [0, f'rgba(5, 193, 240, {opacity})'],
#             [.01, f'rgba(23.846153846153847, 178.15384615384616, 221.53846153846155, {opacity})'],
#             [.1, f'rgba(42.69230769230769, 163.30769230769232, 203.0769230769231, {opacity})'],
#             [.2, f'rgba(61.53846153846154, 148.46153846153845, 184.6153846153846, {opacity})'],
#             [.3, f'rgba(80.38461538461539, 133.6153846153846, 166.15384615384616, {opacity})'],
#             [.4, f'rgba(99.23076923076923, 118.76923076923077, 147.6923076923077, {opacity})'],
#             [.5, f'rgba(118.07692307692308, 103.92307692307692, 129.23076923076923, {opacity})'],
#             [.6, f'rgba(136.92307692307693, 89.07692307692307, 110.76923076923077, {opacity})'],
#             [.7, f'rgba(155.76923076923077, 74.23076923076923, 92.30769230769232, {opacity})'],
#             [.8, f'rgba(174.6153846153846, 59.38461538461539, 73.84615384615387, {opacity})'],
#             [.9, f'rgba(193.46153846153845, 44.53846153846155, 55.384615384615415, {opacity})'],
#             # ['rgba(212.30769230769232, 29.69230769230768, 36.923076923076934, .6)'],
#             # ['rgba(231.15384615384616, 14.84615384615384, 18.46153846153848, .6)'],
#             [1, f'rgba(250, 0, 0, {opacity})']]
# }


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
        debug=True)
    #     host='127.0.0.1',
    #     port='7080',
    #     use_reloader=False,
    #     dev_tools_ui=True,
    #     dev_tools_prune_errors=True
    # )
