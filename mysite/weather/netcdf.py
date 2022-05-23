import logging

import netCDF4 as nc
import numpy as np
import pandas as pd
import shutil

from common import VARIABLES

logging.basicConfig(level=logging.INFO)


def define_netcdf(filepath):
    fn = '/Users/jpy/PycharmProjects/canadian_model/archive/pakistan/test.nc'
    ds = nc.Dataset(filepath, 'w', format='NETCDF4')

    return ds


def variable_subset(df, variable):
    """
    gets a subset of the whole df for a single variable
    :param df:
    :param variable:
    :return:
    """
    cols_to_subset = ['latitude', 'longitude']
    for col in df.columns:
        if col.startswith(variable) and not col.endswith('binned'):
            cols_to_subset.append(col)

    subset = df[cols_to_subset]

    subset[['0', '120', '240']] = [0, 120, 240]

    return subset


def concat_column(subset, variable):
    var_120 = subset[[f'{variable}_120', '120', 'latitude', 'longitude']]
    var_240 = subset[[f'{variable}_240', '240', 'latitude', 'longitude']]

    var_120.columns = [variable, 'hour', 'latitude', 'longitude']
    var_240.columns = [variable, 'hour', 'latitude', 'longitude']

    if variable != 'prate':
        var_0 = subset[[f'{variable}_0', '0', 'latitude', 'longitude']]
        var_0.columns = [variable, 'hour', 'latitude', 'longitude']
    else:
        var_0 = pd.DataFrame(data=None, columns=var_120.columns, index=var_120.index)

    subset_concat = pd.concat([var_0, var_120, var_240], ignore_index=True)

    return subset_concat


def create_lat_long_df(subset_concat, variable, hour):
    df = subset_concat[subset_concat['hour'] == hour]
    df.sort_values(by=['latitude', 'longitude'], inplace=True)
    df['lat_lon'] = list(zip(df.latitude, df.longitude))

    out = pd.DataFrame(
        {},
        columns=df.longitude.unique(),
        index=df.latitude.unique()
    )

    for lat_lon in df.lat_lon:
        lat = lat_lon[0]
        lon = lat_lon[1]
        #         print(f'lat {lat}')
        #         print(f'lon {lon}')

        out.loc[lat, lon] = df.loc[(df['latitude'] == lat) & (df['longitude'] == lon)][variable].item()

    return out


def full_coordinate_process(df, variable):
    lat_unique = df.latitude.unique()
    lon_unique = df.longitude.unique()
    subset = variable_subset(df, variable)
    subset_concat = concat_column(subset, variable)

    array = np.full(shape=(3, len(lat_unique), len(lon_unique)), fill_value=np.nan)

    if variable != 'prate':
        var_0 = create_lat_long_df(subset_concat, variable, 0)
        var_0_array = var_0.to_numpy()
        array[0] = var_0_array
    else:
        pass

    var_120 = create_lat_long_df(subset_concat, variable, 120)
    var_240 = create_lat_long_df(subset_concat, variable, 240)

    var_120_array = var_120.to_numpy()
    var_240_array = var_240.to_numpy()

    array[1] = var_120_array
    array[2] = var_240_array

    return array


def configure_netcdf(df, filepath):
    #     try:
    ds = define_netcdf(filepath)

    df.sort_values(by=['latitude', 'longitude'], inplace=True)

    # TODO: increase dimension number
    forecast_hour_dim = ds.createDimension('forecast_hour', len(VARIABLES.keys()))
    lat_dim = ds.createDimension('lat', len(df.latitude.unique()))
    lon_dim = ds.createDimension('lon', len(df.longitude.unique()))

    latitudes = ds.createVariable('lat', np.float32, ('lat',))
    longitudes = ds.createVariable('lon', np.float32, ('lon',))
    t2m = ds.createVariable('t2m', np.float32, ('forecast_hour', 'lat', 'lon',))
    si10 = ds.createVariable('si10', np.float32, ('forecast_hour', 'lat', 'lon',))
    sde = ds.createVariable('sde', np.float32, ('forecast_hour', 'lat', 'lon',))
    prate = ds.createVariable('prate', np.float32, ('forecast_hour', 'lat', 'lon',))
    hours = ds.createVariable('forecast_hour', np.float32, ('forecast_hour',))

    lats = df.latitude.unique()
    lons = df.longitude.unique()
    latitudes[:] = lats
    longitudes[:] = lons
    hours[:] = [int(x) for x in list(VARIABLES.keys())]

    return ds


def write_variables(df, ds):
    logging.info('starting arrays')
    array_prate = full_coordinate_process(df, 'prate')
    logging.info('done prate')

    array_t2m = full_coordinate_process(df, 't2m')
    logging.info('done t2m')

    array_si10 = full_coordinate_process(df, 'si10')
    logging.info('done si10')

    array_sde = full_coordinate_process(df, 'sde')
    logging.info('done sde')

    ds.variables['t2m'][:,:,:] = array_t2m
    ds.variables['si10'][:,:,:] = array_si10
    ds.variables['sde'][:,:,:] = array_sde
    ds.variables['prate'][:,:,:] = array_prate

    return ds


def main(path, country, project_root_path):
    df = pd.read_csv(f'{project_root_path}/canadian_model/mysite/live_data/{country}/{country}.csv')
    logging.info(f'configuring ds for {country}')
    ds = configure_netcdf(df, path)
    logging.info(f'ds configured for {country}')
    assert ds.isopen() == True
    ds = write_variables(df, ds=ds)
    logging.info(f'done writing variables for {country}')
    logging.info(f'closing ds for {country}')
    ds.close()
    shutil.copyfile(path, f'{project_root_path}/canadian_model/mysite/live_data/{country}/netcdf/netcdf.nc')


if __name__ == '__main__':
    PROJECT_ROOT_PATH = '/Users/jpy/PycharmProjects'
    country = 'pakistan'
    main(
        path=f'{PROJECT_ROOT_PATH}/canadian_model/archive/{country}/netcdf/2022041700"_P"240.nc',
        country=country,
        project_root_path=PROJECT_ROOT_PATH
    )