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
    df_to_gdf
    )
from mysite.weather.file_download import full_download
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import geopandas as gpd
import geojson
import json
from urllib.request import urlopen

from django_plotly_dash import DjangoDash
import plotly.express as px
import plotly.graph_objects as go
# from dash_app_code import token

app = dash.Dash(__name__)

token = 'pk.eyJ1Ijoiam9lLXAteW91bmc5NiIsImEiOiJja3p4aGs3YjUwMWo3MnVuNmw2eDQxaTUzIn0.zeqhZg0rX0uY7C0oVktNjA'

px.set_mapbox_access_token(token)

nb_gjson = read_provinces_gjson('https://gnb.socrata.com/api/geospatial/js6t-a99d?method=export&format=GeoJSON')
nb_gdf = read_provinces_geopands('/Users/jpy/Downloads/1_20,000 Grid _ Grille 1_20,000.geojson')

country = 'canada'
df = pd.read_csv(
    f'/Users/jpy/PycharmProjects/canadian_model/saved_data/{country}/2022-02-23_17-17-24.csv')
gdf = df_to_gdf(df)

print("joining gdfs")
joined_df = gpd.sjoin(nb_gdf, gdf, how='left')

# aggregate data on keyword
data_grouped = joined_df.dropna()
data_grouped = data_grouped.groupby('keyword')[['t2m', 'prate', 'si10', 'sde']].agg(['mean'])
data_grouped.reset_index(inplace=True, drop=False)
data_grouped.columns = ["_".join(a) for a in data_grouped.columns.to_flat_index()]

print('done with data')
print('making plot')
fig = px.choropleth_mapbox(
    data_grouped,
    geojson=nb_gjson,
    locations="keyword_",
    featureidkey='properties.keyword',
    color="t2m_mean",
    mapbox_style="open-street-map",
    opacity=.8,
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
    dcc.Graph(figure=fig)
])
if __name__ == '__main__':
    app.run_server(debug=True)