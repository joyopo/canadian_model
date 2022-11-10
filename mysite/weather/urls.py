from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),
    path('pakistan_grid_dash_plot', views.pakistan_grid, name='pakistan plot'),
    path('canadian_watersheds_dash_plot', views.canadian_watersheds, name='canadian_watersheds'),
    path('canadian_grid_dash_plot', views.canadian_grid, name='canadian_grid'),
    path('pakistan_watersheds_dash_plot', views.pakistan_watersheds, name='pakistan_watersheds'),
    path('about', views.about, name='about'),
    path('download_t2m_240', views.download_t2m_240, name='t2m download'),
    path('pakistan_grid_netcdf', views.download_pakistan_grid_netcdf, name='pakistan_grid_netcdf'),
    path('canada_grid_netcdf', views.download_canada_grid_netcdf, name='canada_grid_netcdf')

]

