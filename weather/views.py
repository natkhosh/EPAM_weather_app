from django.views.generic import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from weather.forms import CityForm, StartDateForm, EndDateForm
from weather.models import City
from weather.parser import data_calculation, weather_data


def get_data(request):
    """
    This function showing the main page of the website
    :param request:
    :return:
    """
    city_name = CityForm()
    start_date = StartDateForm()
    end_date = EndDateForm()
    return render(request, "main_page.html", {
        "city_name": city_name,
        "start_date": start_date,
        "end_date": end_date})


def city(request):
    if request.method == "POST":
        city_name_form = CityForm(request.POST)
        start_date_form = StartDateForm(request.POST)
        end_date_form = EndDateForm(request.POST)
        if city_name_form.is_valid() and \
                start_date_form.is_valid() and \
                end_date_form.is_valid():
            weather_data(request.POST)

            # info_from_site = get_weather_from_api(request)
            # upload_data_to_base(info_from_site.json())
            context = data_calculation(request)
            return render(request, "statistic.html", context)
    else:
        city_name = CityForm()
        start_date = StartDateForm()
        end_date = EndDateForm()
        return HttpResponseRedirect(reverse("main/", {
            "city_name": city_name,
            "start_date": start_date,
            "end_date": end_date
        }))
