from dash import dash_table, callback_context, dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import json
from django_plotly_dash import DjangoDash
import plotly.express as px

from .common import generate_plot_labels, generate_slider_marks, grid_layout, watershed_layouts, \
    filter_and_download_watershed, update_datatable_row, append_datatable_row

# from mysite.weather.common import generate_plot_labels, generate_slider_marks, grid_layout, watershed_layouts, \
#     filter_and_download_watershed, update_datatable_row, append_datatable_row

# from . import file_download



token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'
px.set_mapbox_access_token(token)


app = DjangoDash('canadian_watersheds')
# app = dash.Dash(__name__)

country = 'canada'

print("reading geojson")
# with open('/Users/jpy/Documents/drainage_boundaries_simplifiedpoint2.geojson') as f:
#     drainage_gjson = json.load(f)

with open('/Users/jpy/Documents/weather_portal/mapshaper_simplified/canadian_watersheds.geojson') as f:
    watersheds = json.load(f)
print("finished reading geojsons")


print('reading in csv data')

watershed_data_grouped = pd.read_csv(f'/Users/jpy/PycharmProjects/canadian_model/mysite/live_data/canada/aggregated/watersheds/watersheds.csv')

print('making labels')
labels = generate_plot_labels()
slider_marks, dummy_code_hours = generate_slider_marks()
start_time = watershed_data_grouped['valid_time_0'][0]
layout = watershed_layouts(slider_marks, start_time)


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
    if kwargs['callback_context'].triggered[0]['prop_id'] == 'choropleth.clickData':
        json_string = json.dumps(clickdata)
        clickdata = json.loads(json_string)

        data_table_columns, existing_data = append_datatable_row(
            variable=variable,
            hour=hour,
            clickdata=clickdata,
            existing_data=existing_data,
            df=watershed_data_grouped,
            dummy_code_hours=dummy_code_hours
        )

    if kwargs['callback_context'].triggered[0]['prop_id'] in ['weather-dropdown.value', 'hour-slider.value']:
        if len(existing_data) > 0:
            data_table_columns, existing_data = update_datatable_row(
                variable=variable,
                hour=hour,
                existing_data=existing_data,
                df=watershed_data_grouped,
                dummy_code_hours=dummy_code_hours
            )
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
)
def filter_and_download(n_clicks, data, variable):
    if n_clicks is not None:
        download_df = filter_and_download_watershed(
            data=data,
            variable=variable,
            df=watershed_data_grouped
        )

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
        zoom=2,
        center={'lat': 60, 'lon': -100},
        height=800,
        # width=1000,
        labels=labels,
        hover_data=['HYBAS_ID', f'{variable}_{dummy_code_hours[hour]}'],
        # title='Weather variables aggregated over level 6 Pfafstetter watershed boundaries'

    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=.5
    )

    fig.update_layout(
        autosize=True,
    )

    fig.update_coloraxes(
        colorbar_orientation='h',
        colorbar_title_side='top'

    )

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
        host='127.0.0.1',
        port=8050,
        debug=True
        # use_reloader=False,
        # dev_tools_ui=True,
        # dev_tools_prune_errors=True
    )