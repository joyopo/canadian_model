import datetime
import json
import logging
import ipdb

import pandas as pd
from dash import dash_table, dcc, html

PROJECT_ROOT_PATH = '/Users/jpy/PycharmProjects'

COUNTRIES = ['pakistan', 'canada']

VARIABLE_ABRV = {
    't2m': {
        'name': '2m Surface Temperature',
        'units': 'celsius'
    },
    'si10': {
        'name': 'Wind Speed',
        'units': 'meters/second'
    },
    'sde': {
        'name': 'Snow Depth',
        'units': 'meters'
    },
    'prate': {
        'name': 'Surface Precipitation Rate',
        'units': 'kg m-2 sec-1'
    },

}

time_steps = ['003', '006', '009', '012', '015', '018', '021', '024', '036', '048', '060', '072', '120', '168', '240']

VARIABLES = {
    '000':
        (
            ['TMP_TGL_2', 'temp'],
            ['WIND_TGL_10', 'wind_speed'],
            ['SNOD_SFC_0', 'snow_depth']
        )
}

forecast_hour_variables = (
    ['PRATE_SFC_0', 'precipitation_rate'],
    ['TMP_TGL_2', 'temp'],
    ['WIND_TGL_10', 'wind_speed'],
    ['SNOD_SFC_0', 'snow_depth']
)

for hr in time_steps:
    VARIABLES[hr] = forecast_hour_variables



def generate_plot_labels():
    """
    generate labels for plots. Call this function from dash_app to create label dictionary
    :return:
    """
    plot_labels = {}
    column_names = VARIABLE_ABRV.keys()
    # ['t2m', 'si10', 'sde', 'prate']

    hour_forecast_text = {}

    for hour in [int(x) for x in list(VARIABLES.keys())]:
        hour_forecast_text[hour] = f'{hour} hr Forecast'
        for variable in column_names:
            plot_labels[
                f'{variable}_{hour}'] = f'{hour_forecast_text[hour]} | {VARIABLE_ABRV[variable]["name"]} ({VARIABLE_ABRV[variable]["units"]})'

    return plot_labels


def generate_slider_marks():
    mark_style = {"writing-mode": "vertical-rl",
                  "color": 'black'}
                  # "font-weight": 'bold'}
    marks = {}
    for hour in [int(x) for x in list(VARIABLES.keys())]:
        if hour == 72:
            marks[hour] = {"label": f'3 days', "style": mark_style}
        elif hour == 168:
            marks[hour] = {"label": '1 week', "style": mark_style}
        elif hour == 240:
            marks[hour] = {"label": '10 days', "style": mark_style}
        else:
            marks[hour] = {"label": f'{hour} hours', "style": mark_style}

    # create dictionary that translates dummy code integer to the actual hour
    dummy_code_hours = {}
    num_steps = len(list(VARIABLES.keys()))
    i = 0
    hour_steps = [int(x) for x in list(VARIABLES.keys())]

    for x in range(num_steps):
        dummy_code_hours[x] = hour_steps[i]
        i += 1

    # replace the keys in marks dictionary with the dummy keys
    for key in list(dummy_code_hours.keys()):
        marks[key] = marks.pop(dummy_code_hours[key])

    return marks, dummy_code_hours


def generate_radio_options():
    options = []
    for hour in [int(x) for x in list(VARIABLES.keys())]:
        options.append({'label': f'{hour} hours', 'value': hour})

    for i in options:
        if i['value'] == 72:
            i['label'] = '3 days'
        elif i['value'] == 168:
            i['label'] = '1 week'
        elif i['value'] == 240:
            i['label'] = '10 days'
        else:
            pass

    return options


# --------------------- Dash Functions ---------------------
title_background = '#FFFFFF'
container_background = '#c5ccd3'
interaction_color = '#dcf1fd'

pre_style = {
    'padding': 10,
    'background-color': title_background
}
dropdown_style = {'marginBottom': 20,
                  'background-color': interaction_color,
                  'color': 'black'}
div_style = {
    'border': '2px white solid',
    'padding': 10,
    'background-color': container_background,
    'margin-bottom': 10,
    'margin-top': 10

}
slider_style = {
    'border': '1px grey solid',
    'padding': 10,
    'marginBottom': 20,
    'height': 60,
    'white-space': 'nowrap',
    'background-color': interaction_color,
}
button_style = {
    # 'border': '1px grey solid',
    'padding': 10,
    'marginBottom': 20,
    'background-color': interaction_color

    # 'marginTop': 10
}
section_style = {
    'display': 'inline-block',
    # 'height': '500',
    'vertical-align': 'middle',
    'width': '50%'

    # 'margin': 'auto',
    # 'width': '50%'
}
graph_style = {
    'display': 'inline-block',
    'vertical-align': 'top',
    'border': '1px grey solid',
    'width': '40%',
    'margin-top': 10
}


def grid_layout(slider_marks, forecast_start_time):
    layout = html.Div([
        html.H3(children=f'Forecast hours start from the latest data refresh at: {forecast_start_time} UTC',
                id='forecast_start'),

        html.Div([
            # dropdown and text
            html.Div([
                html.Pre(['Choose a weather variable from the dropdown below to overlay on the map.'],
                         style=pre_style),
                html.Div([dcc.Dropdown(
                    options=[
                        {'label': 'Surface Temperature (celsius)', 'value': 't2m'},
                        {'label': 'Wind Speed (meters/second)', 'value': 'si10'},
                        {'label': 'Snow Depth (meters)', 'value': 'sde'},
                        {'label': 'Surface Precipitation Rate (kg m-2 sec-1)', 'value': 'prate'}
                    ],
                    value='t2m',
                    id='weather-dropdown',
                    placeholder='Select a Weather Variable',
                    style=dropdown_style)]),
            ], style=div_style),

            # slider and text
            html.Div([
                html.Pre(['Adjust the slider below to set the temporal forecast hour.'],
                         style=pre_style),

                html.Div([dcc.Slider(
                    step=1,
                    marks=slider_marks,
                    value=0,
                    id='hour-slider'
                )], style=slider_style),
            ], style=div_style),

            # html.Table([
            #     html.Tr([html.Td(['Latitude']), html.Td(id='lat')]),
            #     html.Tr([html.Td(['Longitude']), html.Td(id='lon')]),
            #     html.Tr([html.Td(['Value']), html.Td(id='val')]),
            #
            # ]),

            # html.Pre(id='click-data'),

            # datatable and text and button
            html.Div([
                html.Pre(['Click a data point on the map to fill in the data table below.'],
                         style=pre_style
                         ),

                dash_table.DataTable(
                    id='data-table',
                    columns=[{
                        'name': 'latitude',
                        'id': 'latitude'
                    }, {
                        'name': 'longitude',
                        'id': 'longitude'
                    }, {
                        'name': 'location_id',
                        'id': 'location_id'
                    }, {
                        'name': 'variable_value',
                        'id': 'variable_value'
                    }],
                    data=[],
                    row_deletable=True,
                    style_cell={'fontSize': 10,
                                'background-color': interaction_color
                                },
                    style_header={'fontWeight': 'bold'}

                ),

                html.Div([
                    html.Button("Download Data", id="btn")
                ], style=button_style),
            ], style=div_style
            ),
        ], style=section_style),
        dcc.Download(id="download"),
        dcc.Store(id='memory'),

        html.Div(
            [
                dcc.Graph(id='choropleth')
            ], style=graph_style)

    ], style={
        'margin': 'auto',
        'width': '100%'}
    )

    return layout


def watershed_layouts(slider_marks, forecast_start_time):
    layout = html.Div([
        html.H3(children=f'Forecast hours start from the latest data refresh at: {forecast_start_time}',
                id='forecast_start'),

        html.Div([
            # dropdown and text
            html.Div([
                html.Pre(['Choose a weather variable from the dropdown below to overlay on the map.'],
                         style=pre_style),

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
                )], style=dropdown_style),
            ], style=div_style),

            # slider and text
            html.Div([
                html.Pre(['Adjust the slider below the map to set the temporal forecast hour.'],
                         style=pre_style),

                html.Div([dcc.Slider(
                    step=1,
                    marks=slider_marks,
                    value=0,
                    id='hour-slider'
                )], style=slider_style),
            ], style=div_style),

            html.Div([
                html.Pre(['Click a data point on the map to fill in the data table below.'],
                         style=pre_style
                         ),

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
                    data=[],
                    row_deletable=True
                ),

                html.Div([
                    html.Button("Download Data", id="btn")
                ], style=button_style),
            ], style=div_style
            ),
        ], style=section_style),
        dcc.Download(id="download"),
        dcc.Store(id='memory'),
        html.Div([dcc.Graph(id='choropleth')],
                 style=graph_style)
    ])

    return layout


def append_datatable_row(variable, hour, clickdata, existing_data, df, dummy_code_hours):
    hybas_id = clickdata['points'][0]['location']
    value = df.loc[(df['HYBAS_ID'] == hybas_id), f'{variable}_{dummy_code_hours[hour]}'].item()
    # 'id' is the row id

    data_column_name = f'{dummy_code_hours[hour]} hr Forecast | {VARIABLE_ABRV[variable]["name"]} ({VARIABLE_ABRV[variable]["units"]})'

    data_table_columns = [
        {
            'name': 'hybas_id',
            'id': 'hybas_id'
        },
        {
            'name': data_column_name,
            'id': data_column_name
        }
    ]

    existing_data.append(
        {
            'hybas_id': hybas_id,
            data_column_name: round(value, 2),
            'id': hybas_id}
    )

    return data_table_columns, existing_data


def update_datatable_row(variable, hour, existing_data, df, dummy_code_hours):
    data_column_name = f'{dummy_code_hours[hour]} hr Forecast | {VARIABLE_ABRV[variable]["name"]} ({VARIABLE_ABRV[variable]["units"]})'

    for i in existing_data:
        hybas_id = i['hybas_id']
        value = df.loc[
            (df['HYBAS_ID'] == hybas_id), f'{variable}_{dummy_code_hours[hour]}'].item()
        i[data_column_name] = round(value, 2)

    data_table_columns = [
        {
            'name': 'hybas_id',
            'id': 'hybas_id'
        },
        {
            'name': data_column_name,
            'id': data_column_name
        }
    ]

    return data_table_columns, existing_data


def append_datatable_row_grid(variable, hour, clickdata, existing_data, df, dummy_code_hours, start_time):
    location = clickdata['points'][0]['location']
    latitude = clickdata['points'][0]['customdata'][0]
    longitude = clickdata['points'][0]['customdata'][1]
    value = df.loc[(df.id == location), f'{variable}_{dummy_code_hours[hour]}'].item()
    # 'id' is the row id

    data_column_name = f'{start_time + datetime.timedelta(hours=dummy_code_hours[hour])} | {VARIABLE_ABRV[variable]["name"]} ({VARIABLE_ABRV[variable]["units"]})'

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
        'name': data_column_name,
        'id': data_column_name
    }]

    existing_data.append(
        {
            'location_id': location,
            'latitude': latitude,
            'longitude': longitude,
            data_column_name: value,
            'id': 0}
    )

    return data_table_columns, existing_data


def update_datatable_row_grid(variable, hour, existing_data, df, dummy_code_hours, start_time):
    data_column_name = f'{start_time + datetime.timedelta(hours=dummy_code_hours[hour])} | {VARIABLE_ABRV[variable]["name"]} ({VARIABLE_ABRV[variable]["units"]})'

    for i in existing_data:
        location = i['location_id']
        value = df.loc[(df.id == location), f'{variable}_{dummy_code_hours[hour]}'].item()
        i[data_column_name] = round(value, 2)

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
        'name': data_column_name,
        'id': data_column_name
    }]
    return data_table_columns, existing_data


def display_click_grid_data_in_datatable(variable, hour, clickdata, df, dummy_code_hours):
    location = clickdata['points'][0]['location']
    latitude = clickdata['points'][0]['customdata'][0]
    longitude = clickdata['points'][0]['customdata'][1]
    value = df.loc[(df.id == location), f'{variable}_{dummy_code_hours[hour]}'].item()
    # data['points'][0]['customdata'][2]
    # 'id' is the row id

    data_column_name = f'{dummy_code_hours[hour]} hr Forecast | {VARIABLE_ABRV[variable]["name"]} ({VARIABLE_ABRV[variable]["units"]})'

    data = [
        {
            'location_id': location,
            'latitude': latitude,
            'longitude': longitude,
            data_column_name: value,
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
        'name': data_column_name,
        'id': data_column_name
    }]

    return data_table_columns, data


def filter_and_download_grid(data, variable, df):
    """

    :param data: data parameter of the datatable
    :param variable: variable from the dropdown
    :param df:
    :return:
    """
    location_ids = []
    for i in data:
        location_ids.append(i['location_id'])

    download_df = pd.DataFrame(data={}, columns=df.columns)
    for i in location_ids:
        filtered_row = df.loc[df['id'] == i]
        download_df = pd.concat([download_df, filtered_row], axis=0)

    # lat = data[0]['latitude']
    # lon = data[0]['longitude']
    # # function to get coordinates of square around click point here
    #
    # lat_lon_list = []
    # lat_lon_list.append([lat, lon])

    # lat_lon_list.append([lat + .15, lon])
    # lat_lon_list.append([lat - .15, lon])
    # lat_lon_list.append([lat, lon + .15])
    # lat_lon_list.append([lat, lon - .15])
    #
    # lat_lon_list.append([lat + .15, lon + .15])
    # lat_lon_list.append([lat - .15, lon - .15])
    # lat_lon_list.append([lat + .15, lon - .15])
    # lat_lon_list.append([lat - .15, lon + .15])

    # download_df = pd.DataFrame(data={}, columns=df.columns)
    # for i in lat_lon_list:
    #     filtered_row = df.loc[(df['latitude'] == i[0]) & (df['longitude'] == i[1])]
    #     download_df = download_df.append(filtered_row)

    # filter download_df to just the variable selected
    cols_to_keep = ['latitude', 'longitude', 'id', 'valid_time_0']
    for col in download_df.columns:
        if col.startswith(variable) and not col.endswith('binned'):
            cols_to_keep.append(col)

    download_df = download_df[cols_to_keep]

    # add 'hours' to end of forecast columns
    for col in download_df.columns:
        if col.startswith(variable):
            download_df = download_df.rename(columns={col: col + ' hour'})

    # reformat columns
    download_df = download_df.rename(columns={'valid_time_0': 'forecast_start_time'})
    download_df.columns = download_df.columns.str.replace(f'{variable}_', '')
    download_df['weather_variable'] = VARIABLE_ABRV[variable]['name']
    download_df['units'] = VARIABLE_ABRV[variable]['units']
    download_df.reset_index(inplace=True, drop=True)
    columns = list(download_df.columns.values)
    columns = columns[-2:] + columns[:-2]
    download_df = download_df[columns]

    return download_df


def filter_and_download_watershed(data, variable, df, hour):
    hybas_ids = []
    for i in data:
        hybas_ids.append(i['hybas_id'])

    download_df = pd.DataFrame(data={}, columns=df.columns)
    for i in hybas_ids:
        filtered_row = df.loc[(df['HYBAS_ID'] == i)]
        download_df = pd.concat([download_df, filtered_row], axis=0)

    # filter download_df to just the variable selected
    cols_to_keep = ['HYBAS_ID', 'valid_time_0']
    for col in download_df.columns:
        if col.startswith(variable) and not col.endswith('binned'):
            cols_to_keep.append(col)

    download_df = download_df[cols_to_keep]

    # add 'hours' to end of forecast columns
    for col in download_df.columns:
        if col.startswith(variable):
            download_df = download_df.rename(columns={col: col + ' hour'})

    download_df.columns = download_df.columns.str.replace(f'{variable}_', '')

    # rename valid_time column
    download_df = download_df.rename(columns={'valid_time_0': 'forecast_start_time'})

    # add clear name and units columns
    download_df['weather_variable'] = VARIABLE_ABRV[variable]['name']
    download_df['units'] = VARIABLE_ABRV[variable]['units']

    download_df.reset_index(inplace=True, drop=True)

    columns = list(download_df.columns.values)

    columns = columns[-2:] + columns[:-2]

    download_df = download_df[columns]

    # TODO: figure out why download file isn't rounding
    download_df = download_df.round(2)

    return download_df


def update_datatable_grid(clickdata, variable, hour, existing_data, df, dummy_code_hours, start_time, **kwargs):
    logging.info(f'kwargs are {kwargs}')
    logging.info(f'callback context: {kwargs["callback_context"]}')
    logging.info(f'callback context attributes: {dir(kwargs["callback_context"])}')

    # ipdb.set_trace()

    if len(kwargs['callback_context'].triggered) > 0:
        triggered_id = kwargs['callback_context'].triggered[0]['prop_id']
        if triggered_id == 'choropleth.clickData':
            json_string = json.dumps(clickdata)
            clickdata = json.loads(json_string)

            data_table_columns, existing_data = append_datatable_row_grid(
                variable=variable,
                hour=hour,
                clickdata=clickdata,
                existing_data=existing_data,
                df=df,
                dummy_code_hours=dummy_code_hours,
                start_time=start_time
            )

        if triggered_id in ['weather-dropdown.value', 'hour-slider.value']:
            if len(existing_data) > 0:
                data_table_columns, existing_data = update_datatable_row_grid(
                    variable=variable,
                    hour=hour,
                    existing_data=existing_data,
                    df=df,
                    dummy_code_hours=dummy_code_hours,
                    start_time=start_time
                )
            else:
                pass
        else:
            pass
    else:
        pass

    return data_table_columns, existing_data
