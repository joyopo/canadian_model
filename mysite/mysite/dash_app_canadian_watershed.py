from mysite.weather.make_plot import (
    make_plot,
    group_data,
    join_provinces,
    process_raw_df,
    read_provinces_gjson,
    read_provinces_geopands,
    read_process_temp,
    geographic_division_ids,
    get_data,
    df_to_gdf,
    spatial_join_and_group
    )
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import geopandas as gpd
import geojson
import json

from django_plotly_dash import DjangoDash
import plotly.express as px


token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

app = dash.Dash(__name__)

# # read in census data
watersheds_gdf = gpd.read_file('/Users/jpy/Downloads/NHN_INDEX_WORKUNIT_LIMIT_2.zip')
# # set crs of census gdf
watersheds_gdf = watersheds_gdf.to_crs("EPSG:4326")
# # test census crs
# assert watersheds_gdf.crs.name == 'WGS 84', f"gdf has crs {watersheds_gdf.crs.name}"
# if watersheds_gdf.crs.name == 'WGS 84':
#     print(f"gdf has crs {watersheds_gdf.crs.name}")
#
# # create geojson file from watershed data and load it to dictionary
# # watersheds_gdf.to_file("mysite/mysite/canadian_watersheds.geojson", driver='GeoJSON')
# with open('/Users/jpy/PycharmProjects/canadian_model/mysite/mysite/canadian_watersheds.geojson') as f:
#     watershed_gjson = json.load(f)
# # gjson = gdf.to_json()
# # gjson_load = json.loads(gjson)
# print("finished loading geojson")
# print(watersheds_gdf.head())
#
# # ----------watersheds-------------
#
# data_df = pd.read_csv('/Users/jpy/PycharmProjects/canadian_model/live_data/canada/canada.csv')
#
# data_gdf = df_to_gdf(data_df)
#
# # sjoin and group
#
# # joined_gdf = gpd.sjoin(watersheds_gdf, data_gdf, how='left')
# # data_grouped = joined_gdf.groupby('')[['t2m', 'prate', 'si10', 'sde']].agg(['mean'])
#
# data_grouped = spatial_join_and_group(data_gdf, watersheds_gdf, 'DATASETNAM')

# data_grouped = pd.read_csv('/Users/jpy/PycharmProjects/canadian_model/mysite/weather/census_subdivision_t2m.csv')
# data_grouped["CSDUID"] = data_grouped["CSDUID"].astype("str")
print(f"finished reading csv")
# print(data_grouped.head())

# print("starting merge")
# gdf_merged = pd.merge(
#     left=data_grouped,
#     right=gdf,
#     how='left',
#     left_on=data_grouped["CSDUID"],
#     right_on=gdf["CSDUID"]
# )
# print("finished merge")
# print(gdf_merged.head())
# print("started making plot")
fig = px.choropleth_mapbox(
    # data_grouped,
    geojson=watersheds_gdf.geometry,
    # locations='DATASETNAM_',
    # featureidkey='properties.DATASETNAM',
    # color="t2m_mean",
    mapbox_style="open-street-map",
    opacity=.5,
    zoom=2,
    center={'lat': 60, 'lon': -100}
       )

#     make_plot(
#     df=gdf_merged,
#     geojson=gdf_merged.geometry,
#     # featureidkey=gdf["CSDUID"],
#     # f"properties.{geographic_division_ids['census_subdivision']}",
#     locations=gdf_merged.index,
# )
print("finished making plot")
print("computing layout")
app.layout = html.Div([
    html.P("Poop:"),
    # dcc.RadioItems(
    #     id='candidate',
    #     options=[{'value': x, 'label': x}
    #              for x in candidates],
    #     value=candidates[0],
    #     labelStyle={'display': 'inline-block'}
    # ),
    dcc.Graph(id="choropleth",
              figure=fig)
])




# fig.update_layout(
#     margin={"r": 0, "t": 0, "l": 0, "b": 0},
#     mapbox_accesstoken=token)


if __name__ == '__main__':
    app.run_server(debug=True)