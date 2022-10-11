from . import file_download
import dash_core_components as dcc
import datetime
from dash.dependencies import Input, Output, State
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px
from django_plotly_dash import DjangoDash
from .common import generate_plot_labels, generate_slider_marks, generate_radio_options, \
    filter_and_download_grid, grid_layout, update_datatable_grid, update_slider_marks

# from mysite.weather.common import generate_plot_labels, generate_slider_marks, generate_radio_options, \
#     display_click_grid_data_in_datatable, filter_and_download_grid, grid_layout, update_datatable_grid

# app = dash.Dash(__name__)
app = DjangoDash('pakistan_grid')

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

px.set_mapbox_access_token(token)

with open('weather/shapefiles/pakistan_grid.geojson') as f:
    pakistan_gjson = json.load(f)
print('done reading gjson')
print('reading live data')
country = 'pakistan'
df = pd.read_csv(
    f'live_data/{country}/{country}.csv')
gdf = file_download.df_to_gdf(df)


# joining grid shapes and data
print("joining gdfs")
grid_gdf = gpd.read_file(f'weather/shapefiles/pakistan_grid.geojson')
joined = gpd.sjoin(gdf, grid_gdf, how='left')
columns = list(gdf.columns) + ['id']
joined = joined[columns]
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

# define layout
grid_layout = grid_layout(slider_marks, start_time_label)

app.layout = grid_layout

print('making plot')

grid_lookup = {feature['properties']['id']: feature for feature in pakistan_gjson['features']}

selections = set()


def get_highlights(selections, geojson=pakistan_gjson, grid_lookup=grid_lookup):
    geojson_highlights = dict()
    for k in geojson.keys():
        if k != 'features':
            geojson_highlights[k] = geojson[k]
        else:
            geojson_highlights[k] = [grid_lookup[selection] for selection in selections]
    return geojson_highlights


@app.callback(
    Output('hour-slider', 'marks'),
    Output('hour-slider', 'value'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'marks'),
    Input('hour-slider', 'value')
)
def update_marks(variable, current_slider_marks, value):
    new_marks, value = update_slider_marks(
        variable=variable,
        slider_marks=current_slider_marks,
        value=value
    )

    return new_marks, value


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


@app.callback(
    Output("choropleth", 'figure'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value'),
    Input('choropleth', 'clickData'),
)
def make_choropleth(variable, hour, clickdata):
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
        labels=labels,
        hover_data=['longitude', 'latitude', f'{variable}_{dummy_code_hours[hour]}'],
        title='Pakistan Grid',
        custom_data=['latitude', 'longitude', f'{variable}_{dummy_code_hours[hour]}']
    )

    fig.update_traces(
        marker_line_width=0,
        autocolorscale=False,
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

    if variable != 't2m':
        fig.update_coloraxes(cmin=1, cmax=joined[f'{variable}_{dummy_code_hours[hour]}'].max(),
                             colorscale=[
                                 [0, 'rgba(13, 8, 135, .6)'],
                                 [.5, '#d8576b'],
                                 [1, "#f0f921"]]
                             )
    else:
        pass

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
            ).data[0],
        )

    fig.update_traces(
        dict(
            marker_line_color='blue',
            marker_line_width=2
        ),
        selector=dict(opacity=.8)
    )

    return fig


print("finished making plot")
print("computing layout")
if __name__ == '__main__':
    app.run_server(
        debug=True)
    #     host='127.0.0.1',
    #     port='7080',
    #     use_reloader=False,
    #     dev_tools_ui=True,
    #     dev_tools_prune_errors=True
    # )
