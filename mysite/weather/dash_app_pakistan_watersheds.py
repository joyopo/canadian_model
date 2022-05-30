import dash_core_components as dcc
import dash_html_components as html
from dash import dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import dash
import geopandas as gpd
import geojson
import json
import pyproj

from django_plotly_dash import DjangoDash
import plotly.express as px
from datetime import datetime

# from .common import generate_plot_labels, generate_slider_marks
from mysite.weather.common import generate_plot_labels, generate_slider_marks, generate_radio_options

# from . import file_download

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'
px.set_mapbox_access_token(token)


# app = DjangoDash('pakistan_watersheds')
app = dash.Dash(__name__)


print("reading geojson")


with open('/Users/jpy/Documents/weather_portal/final_watershed_geojsons/pakistan_watersheds_level7.geojson') as f:
    watersheds = json.load(f)
print("finished reading geojsons")

print('reading in csv data')

country = 'pakistan'
watershed_data_grouped = pd.read_csv(f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/{country}/aggregated/watersheds/watersheds.csv')

print('making labels')
labels = generate_plot_labels()
slider_marks, dummy_code_hours = generate_slider_marks()


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
        step=1,
        marks=slider_marks,
        value=0,
        id='hour-slider'
    )], style={
        'border': '1px grey solid',
        'padding': 10,
        'marginBottom': 20
        # 'marginTop': 10
    }),
    html.Pre('Click a data point on the map to fill in the data table below'),
    dash_table.DataTable(
        id='data-table',
        columns=[
        {
            'name': 'hybas_id',
            'id': 'hybas_id'
        },
        {
            'name': 'variable_value',
            'id': 'variable_value'
        }
    ],
        data=[]
    ),

    html.Button("Download", id="btn"),
    dcc.Download(id="download"),
    dcc.Store(id='memory'),

    html.Div([dcc.Graph(id='choropleth')])]
)
print('finished computing layout')
print('building plot')


# @app.callback(
#     Output('data-table', 'columns'),
#     Input('weather-dropdown', 'value'),
#     Input('hour-slider', 'value')
# )
# def initialize_data_table(variable, hour):
#     data_table_columns = [
#         {
#             'name': 'hybas_id',
#             'id': 'hybas_id'
#         },
#         {
#             'name': f'{variable}_{dummy_code_hours[hour]}',
#             'id': f'{variable}_{dummy_code_hours[hour]}'
#         }
#     ]


@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('choropleth', 'clickData'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value'),
    State('data-table', 'data')

)
def display_click_data(clickdata, variable, hour, existing_data):
    json_string = json.dumps(clickdata)
    data = json.loads(json_string)
    hybas_id = data['points'][0]['location']
    value = watershed_data_grouped.loc[(watershed_data_grouped['HYBAS_ID'] == hybas_id), f'{variable}_{dummy_code_hours[hour]}'].item()
    # 'id' is the row id
    existing_data.append(
        {
            'hybas_id': hybas_id,
            f'{variable}_{dummy_code_hours[hour]}': value,
            'id': hybas_id}
    )
    data_table_columns = [
        {
            'name': 'hybas_id',
            'id': 'hybas_id'
        },
        {
            'name': f'{variable}_{dummy_code_hours[hour]}',
            'id': f'{variable}_{dummy_code_hours[hour]}'
        }
    ]

    return data_table_columns, existing_data


@app.callback(
    Output('download', 'data'),
    Input('btn', 'n_clicks'),
    State('data-table', 'data'),
    State('weather-dropdown', 'value'),
)
def filter_and_download(n_clicks, data, variable):
    hybas_ids = []
    for i in data:
        hybas_ids.append(i['hybas_id'])

    download_df = pd.DataFrame(data={}, columns=watershed_data_grouped.columns)
    for i in hybas_ids:
        filtered_row = watershed_data_grouped.loc[(watershed_data_grouped['HYBAS_ID'] == i)]
        download_df = download_df.append(filtered_row)


    # filter download_df to just the variable selected
    cols_to_keep = ['HYBAS_ID', 'valid_time_0']
    for col in download_df.columns:
        if col.startswith(variable) and not col.endswith('binned'):
            cols_to_keep.append(col)

    download_df = download_df[cols_to_keep]

    # add 'hours' to end of forecast columns
    for col in download_df.columns:
        if col.startswith(variable):
            download_df = download_df.rename(columns={col: col + '_hours'})

    # rename valid_time column
    download_df = download_df.rename(columns={'valid_time_0': 'forecast_start_time'})

    # columns_to_transpose = []
    # for col in download_df_f:
    #     if col.startswith('t2m'):
    #         columns_to_transpose.append(col)
    # df_to_transpose = download_df_f[columns_to_transpose]
    # download_df_f = download_df_f.drop(columns_to_transpose)

    # return download_df.to_dict()
    return dcc.send_data_frame(download_df.to_csv, f'{country}_watersheds_weather_portal.csv')


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
        color=f'{variable}_{dummy_code_hours[hour]}',
        mapbox_style="satellite-streets",
        opacity=.65,
        zoom=4,
        center={'lat': 30, 'lon': 68},
        height=800,
        width=1000,
        labels=labels,
        hover_data=['HYBAS_ID', f'{variable}_{dummy_code_hours[hour]}'],
        title='Weather variables aggregated over level 7 Pfafstetter watershed boundaries'

    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=.5
    )

    fig.update_layout(
        autosize=True,
    )

    return fig


if __name__ == '__main__':
    app.run_server(
        debug=True)
    #     host='127.0.0.1',
    #     port=8052,
    #     use_reloader=False,
    #     dev_tools_ui=True,
    #     dev_tools_prune_errors=True
    # )