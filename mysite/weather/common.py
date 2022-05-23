PROJECT_ROOT_PATH = '/Users/jpy/PycharmProjects'

COUNTRIES = ['pakistan', 'canada']

VARIABLE_ABRV = {
    'prate': 'precipitation_rate',
    't2m': 'temp',
    'si10': 'wind_speed',
    'sde': 'snow_depth'
}

time_steps = ['003', '006', '009', '012', '015', '018', '021', '024', '036', '048', '060', '072', '168', '240']

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

    for hr in time_steps:
        hour_forecast_text[hr] = f'{hr} hr Forecast'

    label_options = {
        't2m': '2m Surface Temperature (celsius)',
        'si10': 'Wind Speed (meters/second)',
        'sde': 'Snow Depth (meters)',
        'prate': 'Surface Precipitation Rate (kg m-2 sec-1)',
    }
    for hour in [int(x) for x in list(VARIABLES.keys())]:
        for variable in column_names:
            plot_labels[f'{variable}_{hour}'] = f'{hour_forecast_text[hour]} | {label_options[variable]}'

    return plot_labels