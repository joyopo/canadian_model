import json
from datetime import datetime, timedelta
import os
import pandas as pd
import geopandas as gpd
import xarray as xr
import logging
import time
# swap imports for dash

# from . import make_plot  # , netcdf
from mysite.weather import make_plot
from mysite.weather.common import COUNTRIES, VARIABLES, base_dir
# from .common import COUNTRIES, VARIABLES, base_dir

logging.basicConfig(level=logging.INFO)

BINS = {
    't2m': {
        'bins': [-100, -30, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 100],
        'labels': [
            '< -30 C',
            '-30 to -20 C',
            '-20 to -15 C',
            '-15 to -10 C',
            '-10 to -5 C',
            '-5 to 0 C',
            '0 to 5 C',
            '5 to 10 C',
            '10 to 15 C',
            '15 to 20 C',
            '20 to 25 C',
            '25 to 30 C',
            '30 to 35 C',
            '> 35 C'

        ]
    },
    'si10': {
        'bins': [-.1, .1, 5, 10, 15, 20, 25, 30, 100],
        'labels': [
            '0',
            '.1 to 5 m/s',
            '5 to 10 m/s',
            '10 to 15 m/s',
            '15 to 20 m/s',
            '20 to 25 m/s',
            '25 to 30 m/s',
            '> 100 m/s'

        ]
    },
    'sde': {
        'bins': [-.1, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.2, 1.4, 1.6, 1.8, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100],
        'labels': [
            '0 to .1 m',
            '.1 to .2 m',
            '.2 to .3 m',
            '.3 to .4 m',
            '.4 to .5 m',
            '.5 to .6 m',
            '.6 to .7 m',
            '.7 to .8 m',
            '.8 to .9 m',
            '.9 to 1 m',
            '1 to 1.2 m',
            '1.2 to 1.4 m',
            '1.4 to 1.6 m',
            '1.6 to 1.8 m',
            '1.8 to 2 m',
            '2 to 3 m',
            '3 to 4 m',
            '4 to 5 m',
            '5 to 6 m',
            '6 to 7 m',
            '7 to 8 m',
            '8 to 9 m',
            '9 to 10 m',
            '> 10 m',

        ]
    },
    'prate': {
        'bins': [-.1, .0001, .0002, .0003, .0004, .0005, .0006, .0007, .0008, .0009, .001, .0015, .0025, 1],
        'labels': [
            '0 to .0001 kg m-2 sec-1',
            '.0001 to .0002 kg m-2 sec-1',
            '.0002 to .0003 kg m-2 sec-1',
            '.0003 to .0004 kg m-2 sec-1',
            '.0004 to .0005 kg m-2 sec-1',
            '.0005 to .0006 kg m-2 sec-1',
            '.0006 to .0007 kg m-2 sec-1',
            '.0007 to .0008 kg m-2 sec-1',
            '.0008 to .0009 kg m-2 sec-1',
            '.0009 to .001 kg m-2 sec-1',
            '.001 to .0015 kg m-2 sec-1',
            '.0015 to .0025 kg m-2 sec-1',
            '> .0025 kg m-2 sec-1',

        ]
    }
}


def df_to_gdf(df):
    """
    :param df: df must have columns 'latitude' and 'longitude'
    :return: geodataframe with points geomoetry
    """
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']))
    gdf = gdf.set_crs(epsg=4326)

    return gdf


PAKISTAN_BOUNDS = {
    'country': 'pakistan',
    'MIN_LONG': 60,
    'MAX_LONG': 76,
    'MIN_LAT': 22,
    'MAX_LAT': 39
}

CANADA_BOUNDS = {
    'country': 'canada',
    'MIN_LONG': -140.99778,
    'MAX_LONG': -52.6480987209,
    'MIN_LAT': 41.6751050889,
    'MAX_LAT': 83.23324
}

BOUNDS = {
    # 'canada': {
    #     'MIN_LONG': -140.99778,
    #     'MAX_LONG': -52.6480987209,
    #     'MIN_LAT': 41.6751050889,
    #     'MAX_LAT': 83.23324
    # },

    'pakistan': {
        'MIN_LONG': 60,
        'MAX_LONG': 76,
        'MIN_LAT': 22,
        'MAX_LAT': 39
    }
}


def read_country_border(country):
    with open('canada_borders.geojson') as f:
        canada_gjson = json.load(f)
    pakistan_gdf = gpd.read_file('mysite/weather/shapefiles/pak_adm_ocha_pco_gaul_20181218_SHP/admin0')

    return canada_gjson


# filenames are independent of country
def get_file_list(forecast_hour, current_day_utc, model_run_start: str):
    file_list = []
    for i in VARIABLES[forecast_hour]:
        variable = i[0]
        variable_folder = i[1]
        filename = f"CMC_glb_{variable}_latlon.15x.15_{current_day_utc}{model_run_start}_P{forecast_hour}.grib2"
        # create list of lists
        file_list.append(
            [
                filename,
                variable_folder,
                forecast_hour,
                model_run_start
            ]
        )

    logging.info("created file_list")
    return file_list


def fetch_grib2(file_list, country: str = 'canada'):

    countries = list(BOUNDS.keys())
    if country not in countries:
        raise ValueError(f"acceptable values for country are {list(BOUNDS.keys())}")

    filepaths = []
    for i in file_list:
        filename = i[0]
        variable_folder = i[1]
        forecast_hour = i[2]
        model_run_start = i[3]
        base_url = f'http://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{model_run_start}/{forecast_hour}/'
        filepath = os.path.join(base_dir, f"grib2/{country}/{variable_folder}/")
        if not os.path.isfile(os.path.join(filepath, filename)):
            logging.info(f'saving grib files for {country}')
            os.system(f"wget {base_url}{filename} -P {filepath}")

        filepaths.append(
            [
                os.path.join(filepath, filename),  # full absolute filepath
                forecast_hour
            ]
        )
    logging.info("finished downloading grib2")
    return filepaths, country


def grib_to_df(filepaths: list, country: str):
    """
    opens the grib data for each variable and creates a dataframe with final columns
    :param filepaths: list of filepaths to grib2 files for each variable
    :param country:
    :return: list of dataframes for each variable
    """
    countries = list(BOUNDS.keys())
    if country not in countries:
        raise ValueError(f"acceptable values for country are {list(BOUNDS.keys())}")
    df_list = []

    bounds = BOUNDS[country]
    logging.info(f'bounding data for {country}')

    for path in filepaths:

        filepath = path[0]
        forecast_hour = int(path[1])

        # open grib2 file in python

        ds = xr.open_dataset(filepath, engine='cfgrib')

        # filter ds to data array of variable
        variable = list(ds.data_vars.keys())[0]
        ds = ds[variable]

        # convert to df
        df = ds.to_dataframe()

        # get lat and lon from index
        df = df.reset_index(drop=False)

        # bound df to country
        df = df[(df["latitude"] >= bounds['MIN_LAT']) & (df["latitude"] <= bounds['MAX_LAT']) & (df["longitude"] >= bounds['MIN_LONG']) & (df["longitude"] <= bounds['MAX_LONG'])]

        # format columns
        df.rename(
            columns={
                'valid_time': f'valid_time_{forecast_hour}',
                variable: f'{variable}_{forecast_hour}'
            },
            inplace=True)
        df['longitude'] = df['longitude'].round(3)
        df['latitude'] = df['latitude'].round(3)

        # TODO: when creating netcdf files, each dimension will need to have the {variable}_forecast_hour column
        # df[f'{variable}_forecast_hour'] = path[1]

        # convert temperature to Celsius
        if variable == 't2m':
            df[f't2m_{forecast_hour}'] = df[f't2m_{forecast_hour}'] - 273.15
        else:
            pass

        # discretize numerical weather data into bins
        # bins = BINS[variable]['bins']
        # labels = BINS[variable]['labels']
        # df[f'{variable}_{forecast_hour}_binned'] = pd.cut(
        #     df[f'{variable}_{forecast_hour}'],
        #     bins=bins,
        #     labels=labels
        # )
        cols_to_keep = ['latitude', 'longitude', f'{variable}_{forecast_hour}', f'valid_time_{forecast_hour}'] # , f'{variable}_{forecast_hour}_binned']
        df = df[df.columns.intersection(cols_to_keep)]
        logging.info(f"processed data from {filepath}")
        df_list.append([df, forecast_hour])

    logging.info('finished creating df_list')
    return df_list


def combine_dfs(df_list):
    """
    Merges variables from separate dataframes together
    :param df_list:
    :return: merged dataframe
    """
    hour = df_list[0][1]

    # set index for the concat
    for df, hour in df_list:
        df.set_index(['latitude', 'longitude'], inplace=True)

    # drop 'valid_time' from all dfs but one to prevent duplicate columns
    for i in range(1, len(df_list)):
        df_list[i][0] = df_list[i][0].drop(f'valid_time_{hour}', axis=1)

    df_list = [df_list[i][0] for i in range(len(df_list))]

    df_combined = pd.concat(df_list, axis=1)

    logging.info(f'finished combining {len(df_list)} dfs')
    return df_combined


def combine_forecast_hours(country: str):
    d = dict()
    forecast_hours = list(VARIABLES.keys())
    for forecast_hour in forecast_hours:
        d[forecast_hour] = pd.read_csv(os.path.join(base_dir, f'live_data/{country}/{forecast_hour}/{forecast_hour}_{country}.csv'))

    df_list = []

    for key, val in d.items():
        val.set_index(['latitude', 'longitude'], inplace=True)
        df_list.append(val)

    df_combined = pd.concat(df_list, axis=1)
    df_combined.reset_index(inplace=True)

    return df_combined


def full_download(forecast_hour: str, country: str, current_day_utc, model_run_start: str):
    file_list = get_file_list(
        forecast_hour=forecast_hour,
        current_day_utc=current_day_utc,
        model_run_start=model_run_start
    )

    filepaths, country = fetch_grib2(
        file_list=file_list,
        country=country,
    )

    df_list = grib_to_df(
        filepaths=filepaths,
        country=country
    )

    df = combine_dfs(
        df_list=df_list
    )

    return df


def bound_to_country(df, country):
    gdf = df_to_gdf(df)
    if country == 'canada':
        polygons = gpd.read_file(os.path.join(base_dir, 'weather/shapefiles/canada_bounds'))
        polygons = polygons.loc[:, ['PRENAME', 'geometry']]
        polygons = polygons.to_crs('EPSG:4326')
        joined_gdf = gpd.sjoin(polygons, gdf, how='left')
        joined_gdf = joined_gdf.drop('geometry', axis=1)
    elif country == 'pakistan':
        polygons = gpd.read_file(os.path.join(base_dir, 'weather/shapefiles/pak_adm_ocha_pco_gaul_20181218_SHP/admin0'))
        joined_gdf = gpd.sjoin(polygons, gdf, how='left')
        joined_gdf = joined_gdf[df.columns]
        joined_gdf = joined_gdf.drop('geometry', axis=1)

    return joined_gdf


def run_aggregations(current_day, model_run_start):
    for country in COUNTRIES:
        # Canada Watersheds
        logging.info('reading live data')
        data = pd.read_csv(os.path.join(base_dir, f'live_data/{country}/{country}.csv'))
        data_gdf = df_to_gdf(data)
        logging.info('reading watershed geofile')
        if country == 'canada':
            data_gdf.drop('index_right', inplace=True, axis=1)
            watershed_gdf = gpd.read_file(os.path.join(base_dir, 'weather/shapefiles/canadian_watersheds.geojson'))
            watershed_gdf = watershed_gdf.set_crs(epsg=4326)
            watershed_grouped = make_plot.spatial_join_and_group(
                data=data_gdf,
                polygons=watershed_gdf,
                column_aggregate='HYBAS_ID'
            )
        elif country == 'pakistan':
            watershed_gdf = gpd.read_file(os.path.join(base_dir, 'weather/shapefiles/pakistan_watersheds_level7.geojson'))
            watershed_gdf = watershed_gdf.set_crs(epsg=4326)
            watershed_grouped = make_plot.spatial_join_and_group(
                data=data_gdf,
                polygons=watershed_gdf,
                column_aggregate='HYBAS_ID'
            )
        else:
            raise Exception
        logging.info('finished spatial join')
        watershed_grouped.to_csv(os.path.join(base_dir, f'archive/{country}/aggregated/watersheds/{current_day}_{model_run_start}.csv'))
        watershed_grouped.to_csv(os.path.join(base_dir, f'live_data/{country}/aggregated/watersheds/watersheds.csv'))


def main():
    current_time_utc = datetime.utcnow()
    current_day_utc = current_time_utc.strftime('%Y%m%d')
    if datetime.utcnow().time() > datetime.strptime('18:00', '%H:%M').time():
        model_run_start = '12'
    elif datetime.utcnow().time() > datetime.strptime('3:00', '%H:%M').time():
        model_run_start = '00'
    else:
        current_time_utc = datetime.utcnow() - timedelta(days=1)
        current_day_utc = current_time_utc.strftime('%Y%m%d')
        model_run_start = '12'
    forecast_hours = list(VARIABLES.keys())
    for country in COUNTRIES:
        for hour in forecast_hours:
            try:
                logging.info(f'trying model_run_start {model_run_start}')
                logging.info(f'trying date {current_day_utc}')
                df = full_download(
                    forecast_hour=hour,
                    country=country,
                    current_day_utc=current_day_utc,
                    model_run_start=model_run_start
                )
                df.to_csv(os.path.join(base_dir, f'live_data/{country}/{hour}/{hour + "_" + country}.csv'))

            except:
                model_run_start = '12'
                current_time_utc = datetime.utcnow() - timedelta(days=1)
                current_day_utc = current_time_utc.strftime('%Y%m%d')
                logging.info(f'excepting model_run_start {model_run_start}')
                logging.info(f'excepting date {current_day_utc}')
                df = full_download(
                    forecast_hour=hour,
                    country=country,
                    current_day_utc=current_day_utc,
                    model_run_start=model_run_start
                )
                df.to_csv(os.path.join(base_dir, f'live_data/{country}/{hour}/{hour + "_" + country}.csv'))

        df_combined_forecast = combine_forecast_hours(country)
        df_combined_forecast = bound_to_country(df_combined_forecast, country)
        # df_combined_forecast.to_csv(
        #     os.path.join(base_dir, f'archive/{country}/csv/{current_day_utc}{model_run_start}_P{hour}.csv'))
        df_combined_forecast.to_csv(os.path.join(base_dir, f'live_data/{country}/{country}.csv'))
        logging.info('writing netcdf')

    logging.info('running aggregations')
    run_aggregations(current_day_utc, model_run_start)
    logging.info('finished aggregating')
    print('done')


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    elapsed_time = end - start
    logging.info(f'elapsed time: {elapsed_time}')
