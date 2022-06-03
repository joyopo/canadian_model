import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash import dash_table

PROJECT_ROOT_PATH = '/Users/jpy/PycharmProjects'

COUNTRIES = ['pakistan', 'canada']

VARIABLE_ABRV = {
    'prate': 'precipitation_rate',
    't2m': 'temp',
    'si10': 'wind_speed',
    'sde': 'snow_depth'
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

    label_options = {
        't2m': '2m Surface Temperature (celsius)',
        'si10': 'Wind Speed (meters/second)',
        'sde': 'Snow Depth (meters)',
        'prate': 'Surface Precipitation Rate (kg m-2 sec-1)',
    }

    for hour in [int(x) for x in list(VARIABLES.keys())]:
        hour_forecast_text[hour] = f'{hour} hr Forecast'
        for variable in column_names:
            plot_labels[f'{variable}_{hour}'] = f'{hour_forecast_text[hour]} | {label_options[variable]}'

    return plot_labels


def generate_slider_marks():
    marks = {}
    for hour in [int(x) for x in list(VARIABLES.keys())]:
        if hour == 72:
            marks[hour] = f'3 days'
        elif hour == 168:
            marks[hour] = '1 week'
        elif hour == 240:
            marks[hour] = '10 days'
        else:
            marks[hour] = f'{hour} hours'

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


def display_click_data_in_datatable(variable, hour, clickdata, df, dummy_code_hours):
    location = clickdata['points'][0]['location']
    latitude = clickdata['points'][0]['customdata'][0]
    longitude = clickdata['points'][0]['customdata'][1]
    value = df.loc[(df.id == location), f'{variable}_{dummy_code_hours[hour]}'].item()
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


def filter_and_download_grid(data, variable, df):
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

    download_df = pd.DataFrame(data={}, columns=df.columns)
    for i in lat_lon_list:
        filtered_row = df.loc[(df['latitude'] == i[0]) & (df['longitude'] == i[1])]
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

    return download_df


def grid_layout(slider_marks):
    layout = html.Div([
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
            row_deletable=True
        ),

        html.Button("Download", id="btn"),
        dcc.Download(id="download"),
        dcc.Store(id='memory'),

        html.Div([dcc.Graph(id='choropleth')])  # style={'display': 'inline-block'}

        ]
    )

    return grid_layout

