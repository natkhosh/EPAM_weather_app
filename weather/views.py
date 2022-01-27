from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from weather.forms import CityForm, EndDateForm, StartDateForm
from weather.util import preparing_data_to_show, weather_data_update


def get_data(request):
    """
    Function shows the main page of the website.
    """
    city_name = CityForm()
    start_date = StartDateForm()
    end_date = EndDateForm()
    return render(request, "main_page.html", {
        "city_name": city_name,
        "start_date": start_date,
        "end_date": end_date})


def statistic(request):
    """
    Function gives information about request city weather between
    date_first and date_last.
    """
    if request.method == "POST":
        city_name_form = CityForm(request.POST)
        start_date_form = StartDateForm(request.POST)
        end_date_form = EndDateForm(request.POST)

        if city_name_form.is_valid() and start_date_form.is_valid() and \
                end_date_form.is_valid():
            weather_data_update(request.POST)
            context = preparing_data_to_show(request)
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


def handler400(request, exception):
    """
    The server has not found anything matching the request.
    """
    return render(request, "400.html", status=400)


def handler404(request, exception):
    """
    The request could not be understood by the server due to malformed syntax.
    """
    return render(request, "404.html", status=404)


def handler500(request):
    """
    The server encountered an unexpected condition which prevented it from
    fulfilling the request.
    """
    return render(request, "500.html")
