import ipdb

from . import file_download
# import mysite.weather.file_download as file_download
import dash_core_components as dcc
import datetime
import dash_html_components as html
from dash import dash_table
import dash

from dash.dependencies import Input, Output, State
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
# from dash_app_code import token
from django_plotly_dash import DjangoDash
from .common import generate_plot_labels, generate_slider_marks, generate_radio_options, \
    display_click_grid_data_in_datatable, filter_and_download_grid, grid_layout, update_datatable_grid

# from mysite.weather.common import generate_plot_labels, generate_slider_marks, generate_radio_options, \
#     display_click_grid_data_in_datatable, filter_and_download_grid, grid_layout, update_datatable_grid

# app = dash.Dash(__name__)
app = DjangoDash('pakistan_grid')

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

px.set_mapbox_access_token(token)

# creating hover labels


with open('/Users/jpy/Documents/pakistan_grid.geojson') as f:
    pakistan_gjson = json.load(f)
# nb_gjson = read_provinces_gjson('https://gnb.socrata.com/api/geospatial/js6t-a99d?method=export&format=GeoJSON')
# pakistan_gdf = gpd.read_file('/Users/jpy/Downloads/pak_adm_ocha_pco_gaul_20181218_SHP/admin2')
# pakistan_json = pakistan_gdf.to_json()
# pakistan_gjson = json.loads(pakistan_json)
print('done reading gjson')
print('reading live data')
country = 'pakistan'
df = pd.read_csv(
    f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/{country}/{country}.csv')
gdf = file_download.df_to_gdf(df)


# joining grid shapes and data
print("joining gdfs")
grid_gdf = gpd.read_file(f'/Users/jpy/Documents/{country}_grid.geojson')
# gdf.drop('index_right', axis=1, inplace=True)
joined = gpd.sjoin(gdf, grid_gdf, how='left')
columns = list(gdf.columns) + ['id']
joined = joined[columns]
# ipdb.set_trace()


print('done with data')
print('making labels')
labels = generate_plot_labels()
radio_options = generate_radio_options()
slider_marks, dummy_code_hours = generate_slider_marks()
print('computing layout')

# define start time
start_time = df['valid_time_0'][0]
try:
    start_time_label = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
except:
    start_time_date = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    start_time_label = datetime.datetime.combine(start_time_date, datetime.datetime.min.time())

# start_time_label = f"{df['valid_time_0'][0]} UTC"
# if ':' not in start_time_label:
#     start_time_label = start_time_label.replace('UTC', '00:00 UTC')

# define layout
grid_layout = grid_layout(slider_marks, start_time_label)

app.layout = grid_layout

print('making plot')

@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('choropleth', 'clickData'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value'),
    State('data-table', 'data')
)
def update_grid_datatable(clickdata, variable, hour, existing_data, **kwargs):
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

# @app.callback(
#     Output('data-table', 'columns'),
#     Output('data-table', 'data'),
#     Input('choropleth', 'clickData'),
#     Input('weather-dropdown', 'value'),
#     Input('hour-slider', 'value')
# )
# def display_click_data(clickdata, variable, hour):
#     json_string = json.dumps(clickdata)
#     data = json.loads(json_string)
#     data_table_columns, data = display_click_grid_data_in_datatable(
#         variable=variable,
#         hour=hour,
#         clickdata=data,
#         df=joined,
#         dummy_code_hours=dummy_code_hours
#     )
#     return data_table_columns, data


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
        height=500,
        # width=1000,
        labels=labels,  # .update({'ADM2_PCODE_': 'Administrative Boundary Code'}),
        hover_data=['longitude', 'latitude', f'{variable}_{dummy_code_hours[hour]}'],
        title='Pakistan Grid',
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
        margin=dict(
            l=10,
            r=10,
            b=10,
            t=10,
        ),
        # sliders=[{'len': 800}, {'lenmode': 'pixels'}]
    )

    fig.update_coloraxes(
        colorbar_orientation='h',
        colorbar_title_side='top'
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

    # ipdb.set_trace()
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
