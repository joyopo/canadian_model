import geopandas as gpd
from geojson import dump
import plotly.express as px
from urllib.request import urlopen
import json


geographic_division_ids = {
    "census_subdivision": "CSDUID",
    "census_tract": "CTUID"
}


def read_provinces_gjson(url):
    with urlopen(url) as response:
        provinces_gjson = json.load(response)

    return provinces_gjson


def read_provinces_geopands(path: str):
    provinces_gdf = gpd.read_file(path)

    return provinces_gdf


def process_raw_df(df):
    cols_to_drop = ['time', 'step', 'heightAboveGround',
                    'valid_time']
    df = df.drop(cols_to_drop, axis=1)
    return df


def df_to_gdf(df):
    """
    :param df: df must have columns 'latitude' and 'longitude'
    :return: geodataframe with points geomoetry
    """
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    gdf = gdf.set_crs(epsg=4326)

    return gdf


def join_provinces(gdf_ca_t2m, provinces_gdf, census_id):
    # join gdfs on geometry columns
    joined_df = gpd.sjoin(gdf_ca_t2m, provinces_gdf, how='left')

    # drop unneeded columns
    data = joined_df[["t2m", "geometry", census_id]]

    return joined_df, data


def group_data(data, column):
    data = data.dropna(inplace=False)
    data_grouped = data.groupby(column)['t2m'].agg(['mean'])

    data_grouped.rename(columns={'mean': 'mean_t2m'}, inplace=True)

    return data_grouped


def spatial_join_and_group(data, polygons, column_aggregate: str):
    # create dictionary of aggregation methods for the columns in data
    aggregation_dictionary = {}
    for column in list(data.columns):
        if column.startswith('valid'):
            # valid_time columns take the first value
            aggregation_dictionary[column] = 'first'
        elif column.endswith('binned'):
            aggregation_dictionary[column] = 'first'
        elif column == 'PRENAME':
            aggregation_dictionary[column] = 'first'
        else:
            # all variable columns are averaged
            aggregation_dictionary[column] = 'mean'

    # columns that do not need to be aggregated
    cols_to_pop = ['Unnamed: 0', 'latitude', 'longitude', 'geometry']
    for key in cols_to_pop:
        # remove unneeded columns from agg dict
        aggregation_dictionary.pop(key, None)

    # join data with polygons
    joined_gdf = gpd.sjoin(polygons, data, how='left')

    # aggregate data on the given column using methods from the aggregation_dictionary
    data_grouped = joined_gdf.groupby(column_aggregate).agg(aggregation_dictionary)

    data_grouped.reset_index(inplace=True, drop=False)
    # data_grouped.columns = ["_".join(a) for a in data_grouped.columns.to_flat_index()]

    return data_grouped


def make_plot(df, geojson, featureidkey, locations):
    fig = px.choropleth_mapbox(df,
                               geojson=geojson,
                               locations=locations,
                               featureidkey=featureidkey,
                               color="mean_t2m",
                               mapbox_style="open-street-map",
                               opacity=1,
                               zoom=2,
                               center={'lat': 60, 'lon': -100}
                               )

    return fig
