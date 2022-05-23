import geopandas as gpd
from geojson import dump
import plotly.express as px
from urllib.request import urlopen
import json


geographic_division_ids = {
    "census_subdivision": "CSDUID",
    "census_tract": "CTUID"
}

# 'https://data.opendatasoft.com/explore/dataset/georef-canada-province@public/download/?format=geojson&timezone=America/New_York&lang=en'
def read_provinces_gjson(url):
    with urlopen(url) as response:
        provinces_gjson = json.load(response)

    return provinces_gjson


# '/Users/jpy/Downloads/georef-canada-province.geojson')
def read_provinces_geopands(path: str):
    provinces_gdf = gpd.read_file(path)

    return provinces_gdf


def process_raw_df(df):
    cols_to_drop = ['time', 'step', 'heightAboveGround',
                    'valid_time']
    df = df.drop(cols_to_drop, axis=1)
    return df


# "/Users/jpy/PycharmProjects/canadian_model/grib2/temperature/CMC_glb_TMP_TGL_2_latlon.15x.15_2022021500_P240.grib2"
# def read_process_temp(path):
#     df = grib_to_df(path)
#     df = process_raw_df(df)  # TODO: specific to data source, consistent columns between variables?
#     gdf_ca_t2m = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
#     gdf_ca_t2m = gdf_ca_t2m.set_crs(epsg=4326)
#
#     return gdf_ca_t2m


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
# lat = df['latitude'].to_list()
# lon = df['longitude'].to_list()
# temp = df['t2m'].to_list()

# gdf = gpd.read_file('/Users/jpy/PycharmProjects/canadian_model/lpr_000b16a_e.zip')

# gdf_ca_t2m = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
# gdf_ca_t2m = gdf_ca_t2m.set_crs(epsg=4326)

# gdf_provinces = gdf.to_crs(epsg=4326)
# gdf_provinces = gdf
# t2m_provinces = gpd.sjoin(gdf_ca_t2m, gdf_provinces, how='left')


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


# fig = px.choropleth_mapbox(data_grouped,
#                            geojson=provinces,
#                            locations=data_grouped.index,
#                            featureidkey="properties.prov_name_en",
#                            color="mean",
# #                            center={"lat": 45.5517, "lon": -73.7073},
#                            mapbox_style="open-street-map",
# #                            zoom=8.5
#                           )
# fig.show()

# def get_data():
#     # read in census data
#     gdf = gpd.read_file('/Users/jpy/Downloads/lcsd000b16a_e.zip')
#     # set crs of census gdf
#     gdf = gdf.to_crs("EPSG:4326")
#     # test census crs
#     assert gdf.crs.name == 'WGS 84', f"gdf has crs {gdf.crs.name}"
#     if gdf.crs.name == 'WGS 84':
#         print(f"gdf has crs {gdf.crs.name}")
#
#     # create geojson file from census data and load it to dictionary
#     gdf.to_file("census_subdivisions.geojson", driver='GeoJSON')
#     gjson = gdf.to_json()
#     gjson_load = json.loads(gjson)
#
#     # read weather test and test CRS
#     df = read_process_temp("/Users/jpy/PycharmProjects/canadian_model/grib2/temperature/CMC_glb_TMP_TGL_2_latlon.15x.15_2022021500_P240.grib2")
#     assert df.crs.name == 'WGS 84', f"df has crs {df.crs.name}"
#     if df.crs.name == 'WGS 84':
#         print(f"df has crs {df.crs.name}")
#
#     # Spatial join of weather points and census division
#     joined_df, data = join_provinces(df, gdf, geographic_division_ids['census_subdivision'])
#
#     print('finished joining data')
#     # aggregate average data for given census division
#     data_grouped = group_data(data, geographic_division_ids['census_subdivision'])
#     print('finished grouping data')
#     data_grouped.to_csv('census_subdivision_t2m.csv')
#
#     return gjson_load, data_grouped

# make plot
# fig = make_plot(
#     df=data_grouped,
#     geojson=gjson_load,
#     featureidkey=f"properties.{geographic_division_ids['census_subdivision']}",
#     locations=data_grouped.index,
# )



# if __name__ == '__main__':
    # TODO: pull file from fetch grib2 function
    # df = read_process_temp("/Users/jpy/PycharmProjects/canadian_model/grib2/temperature/CMC_glb_TMP_TGL_2_latlon.15x.15_2022021500_P240.grib2")
    # provinces_geojson = read_provinces_gjson('https://data.opendatasoft.com/explore/dataset/georef-canada-province@public/download/?format=geojson&timezone=America/New_York&lang=en')
    # provinces_gdf = read_provinces_geopands('/Users/jpy/Downloads/georef-canada-province.geojson')
    # data = join_provinces_and_group(df, provinces_gdf)
    #
    # fig = make_plot(
    #     df=data,
    #     geojson=provinces_geojson,
    #     featureidkey="properties.prov_name_en",
    #     locations=data.index,
    # )

    # gjson_load, data_grouped = get_data()
