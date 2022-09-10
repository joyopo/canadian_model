import datetime
from dash import dcc, callback_context
from dash.dependencies import Input, Output, State
import pandas as pd
import json
from django_plotly_dash import DjangoDash
import plotly.express as px
import logging
from .common import generate_plot_labels, generate_slider_marks, watershed_layouts, \
    filter_and_download_watershed, append_datatable_row_watershed, update_datatable_row_watershed, VARIABLE_ABRV
#
# from mysite.weather.common import generate_plot_labels, generate_slider_marks, watershed_layouts, \
#     filter_and_download_watershed, append_datatable_row, update_datatable_row, VARIABLE_ABRV

# from . import file_download

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'
px.set_mapbox_access_token(token)


app = DjangoDash('pakistan_watersheds')
# app = dash.Dash(__name__)

logging.basicConfig(level=logging.INFO)


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

# forecast start time
start_time = watershed_data_grouped['valid_time_0'][0]
try:
    start_time_label = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
except:
    start_time_date = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    start_time_label = datetime.datetime.combine(start_time_date, datetime.datetime.min.time())


# define app layout
layout = watershed_layouts(slider_marks, start_time_label)

print("computing layout")
app.layout = layout
print('finished computing layout')
print('building plot')


@app.callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('choropleth', 'clickData'),
    Input('weather-dropdown', 'value'),
    Input('hour-slider', 'value'),
    State('data-table', 'data')
)
def update_datatable(clickdata, variable, hour, existing_data, **kwargs):
    logging.info(f'kwargs are {kwargs}')
    logging.info(f'callback context: {kwargs["callback_context"]}')
    logging.info(f'callback context attributes: {dir(kwargs["callback_context"])}')

    if len(kwargs['callback_context'].triggered) > 0:
        triggered_id = kwargs['callback_context'].triggered[0]['prop_id']
        if triggered_id == 'choropleth.clickData':
            json_string = json.dumps(clickdata)
            clickdata = json.loads(json_string)

            data_table_columns, existing_data = append_datatable_row_watershed(
                variable=variable,
                hour=hour,
                clickdata=clickdata,
                existing_data=existing_data,
                df=watershed_data_grouped,
                dummy_code_hours=dummy_code_hours,
                start_time=start_time_label
            )

        if triggered_id in ['weather-dropdown.value', 'hour-slider.value']:
            if len(existing_data) > 0:
                data_table_columns, existing_data = update_datatable_row_watershed(
                    variable=variable,
                    hour=hour,
                    existing_data=existing_data,
                    df=watershed_data_grouped,
                    dummy_code_hours=dummy_code_hours,
                    start_time=start_time_label
                )
            else:
                pass
        else:
            pass
    else:
        pass

    return data_table_columns, existing_data


@app.callback(
    Output('download', 'data'),
    Input('btn', 'n_clicks'),
    State('data-table', 'data'),
    State('weather-dropdown', 'value'),
    State('hour-slider', 'value')
)
def filter_and_download(n_clicks, data, variable, hour):
    if n_clicks is not None:
        download_df = filter_and_download_watershed(
            data=data,
            variable=variable,
            df=watershed_data_grouped,
            hour=hour,
            start_time=start_time_label
        )

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
        height=500,
        title='Pakistan Watersheds',
        labels=labels,
        hover_data=['HYBAS_ID', f'{variable}_{dummy_code_hours[hour]}'],

    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=.5
    )

    fig.update_layout(
        autosize=True,
        margin=dict(
            l=10,
            r=10,
            b=10,
            t=10,
        ),
    )

    fig.update_coloraxes(
        colorbar_orientation='h',
        colorbar_title_side='top'

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
