from django.shortcuts import render
from django.http import HttpResponse, Http404, FileResponse
from . import file_download
from . import dash_app_pakistan_grid
# from . import dash_app_canadian_watersheds
# from . import dash_app_canadian_grid
from . import dash_app_pakistan_watersheds
import os


# Create your views here.
def index(request):
    return HttpResponse("65 hunnid degrees")


def home(request):
    return render(request, 'pakistan_grid.html')


def pakistan_grid(request):
    return render(request, 'pakistan_grid.html')


def pakistan_watersheds(request):
    return render(request, 'pakistan_watersheds.html')


def canadian_watersheds(request):
    return render(request, 'canadian_watershed.html')


def canadian_grid(request):
    return render(request, 'canadian_grid.html')


def about(request):
    return render(request, 'about.html')


def download_pakistan_grid_netcdf(request):
    filename = 'live_data/pakistan/netcdf/netcdf.nc'
    response = FileResponse(open(filename, 'rb'))
    return response


def download_canada_grid_netcdf(request):
    filename = 'live_data/canada/netcdf/netcdf.nc'
    response = FileResponse(open(filename, 'rb'))
    return response

# add parameters for the base url to download specified variables and time forecasts
def download_t2m_240(request):
    variable = "2m Temperature"
    forecast_time = "240 Hours"
    try:
        filepath = file_download.fetch_grib2_file_temp_os()
    except:
        raise Http404("File could not be saved")
    output = f"Downloaded data for weather variable: {variable}, forecasted to {forecast_time}." \
             f"File saved at {filepath}"
    return HttpResponse(output)
