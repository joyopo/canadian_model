from .common import generate_plot_labels, generate_slider_marks, grid_layout, update_datatable_grid, \
    filter_and_download_grid
# from mysite.weather.common import generate_plot_labels, generate_slider_marks, generate_radio_options, \
#     display_click_grid_data_in_datatable, filter_and_download_grid, grid_layout, update_datatable_grid
from . import file_download
# import mysite.weather.file_download as file_download
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import geopandas as gpd
import json
from django_plotly_dash import DjangoDash
import plotly.express as px
import datetime

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'
px.set_mapbox_access_token(token)


app = DjangoDash('canadian_grid')
# app = dash.Dash(__name__)


print("reading geojson")
with open('weather/shapefiles/canada_grid.geojson') as f:
    grid = json.load(f)
print("finished reading geojsons")

print('reading in csv data')
country = 'canada'
df = pd.read_csv(
    f'live_data/{country}/{country}.csv')
print('df to gdf')
gdf = file_download.df_to_gdf(df)
print('done')

grid_gdf = gpd.read_file('weather/shapefiles/canada_grid.geojson')
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


print("computing layout")
grid_layout = grid_layout(slider_marks, start_time_label)

app.layout = grid_layout

grid_lookup = {feature['properties']['id']: feature for feature in grid['features']}

selections = set()


@app.callback(
    Output('hour-slider', 'marks'),
    Input('weather-dropdown', 'value')
)
def update_slider_marks(variable):
    if variable == 'prate':
        slider_marks.pop(0)
    else:
        pass

    return slider_marks

def get_highlights(selections, geojson=grid, grid_lookup=grid_lookup):
    geojson_highlights = dict()
    for k in geojson.keys():
        if k != 'features':
            geojson_highlights[k] = geojson[k]
        else:
            geojson_highlights[k] = [grid_lookup[selection] for selection in selections]
    return geojson_highlights

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
    Input('hour-slider', 'value'),
    Input('choropleth', 'clickData'),

)
def make_choropleth(variable, hour, clickdata):
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
        ),
        uirevision=variable
    )

    fig.update_coloraxes(
        colorbar_orientation='h',
        colorbar_title_side='top'
    )
    
    if clickdata is not None:
        selected_location = clickdata['points'][0]['location']

        if selected_location not in selections:
            selections.add(selected_location)
        else:
            selections.remove(selected_location)

    if len(selections) > 0:
        # highlights contain the geojson information for only
        # the selected watersheds
        highlights = get_highlights(selections)

        fig.add_trace(
            px.choropleth_mapbox(
                joined,
                geojson=highlights,
                color=f'{variable}_{dummy_code_hours[hour]}',
                locations='id',
                featureidkey='properties.id',
                opacity=.8,
                hover_data=['longitude', 'latitude', f'{variable}_{dummy_code_hours[hour]}'],
                custom_data=['latitude', 'longitude', f'{variable}_{dummy_code_hours[hour]}']
            ).data[0]
        )

    fig.update_traces(
        dict(
            marker_line_color='blue',
            marker_line_width=2
        ),
        selector=dict(opacity=.8)
    )
    return fig

print("finished building plot")


if __name__ == '__main__':
    app.run_server(
        debug=True,
        # host='127.0.0.1',
        # port=8055,
        # use_reloader=False,
        # dev_tools_ui=True,
        # dev_tools_prune_errors=True
    )
