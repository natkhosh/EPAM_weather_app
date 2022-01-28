import os
import requests
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from django.db.models import Avg, Count, Max, Min

from .models import City


def checking_city_in_database(city_name):
    """
    Function checks information about the requested city in the database.
    :param city_name: requested city name
    :return: QuerySet of values of the requested city
    """
    return City.objects.filter(city_name__startswith=city_name).values()


def weather_data_update(request):
    """
    Function getting request (requested statistic) and collecting
    information in the next algorithm:
        1) Checking statistic in database. If the statistic is in the database,
         the function checks relevance weather information. If not, save
         data to database;
        2) If the statistic isn't in database, function update database;
        3) If information about the requested statistic is relevant in the
         database, information would get the weather from the database.
    :param request:
        {"city_name": city_name,
        "start_date": start_date,
        "end_date": end_date}
    """
    requested_city = request["form_city"]
    city_check = checking_city_in_database(requested_city)
    requested_date = datetime.strptime(
        request["form_end_date"], '%Y-%m-%d').date()

    if not city_check:
        download_data_batches(request)

    if requested_date > City.objects.filter(
            city_name__startswith=requested_city).last().date:
        # the start date to upload data (last date from db + 1 day)
        request_start_day = City.objects.filter(
            city_name__startswith=requested_city).last().date \
                            + timedelta(days=1)
        request_upd = {
            "form_city": requested_city,
            "form_start_date": request_start_day,
            "form_end_date": request["form_end_date"]}

        download_data_batches(request_upd)


def get_weather_from_api(request_data: dict):
    """
    Function getting data from external site.
    :param request_data: dict - city, start date, end date
    :return: response
    """
    link = "https://api.worldweatheronline.com/premium/v1/past-weather.ashx"
    secret_key = os.environ.get("API_KEY")

    payload = {
        "q": request_data["form_city"],
        "date": request_data["form_start_date"],
        "enddate": request_data["form_end_date"],
        "format": "json",
        "key": secret_key
    }
    response = requests.get(link, params=payload)
    return response


def upload_data_to_base(data):
    """
    Function getting response from site and upload data to database.
    :param data: response from site in json
    """
    city_name = data["data"]["request"][0]["query"]
    for date in data["data"]["weather"]:

        hourly = date["hourly"]
        day_record = City()
        day_record.id = f'{str(date["date"])}-{city_name}'
        day_record.city_name = city_name

        day_record.date = str(date["date"])
        day_record.date_year = str(date["date"][:4])

        day_record.avg_temp = date["avgtempC"]
        day_record.max_temp = date["maxtempC"]
        day_record.min_temp = date["mintempC"]

        day_record.precip_mm = sum([float(time["precipMM"])
                                    for time in hourly]) / len(hourly)

        day_record.most_common_weather = find_most_common_weather(
            [time["weatherDesc"][0]["value"] for time in hourly])

        day_record.wind_direction = find_average_wind_direction(
            [int(time["winddirDegree"]) for time in hourly])

        day_record.wind_speed = sum(
            [int(time["windspeedKmph"]) for time in hourly]) / len(hourly)

        day_record.save()


def download_data_batches(request: dict):
    """
    Function of downloading data in batches, in case of limiting the volume
    of the downloaded site.
    :param request: dict - city, start date, end date
    """

    city = request["form_city"]
    start_date = datetime.strptime(str(request["form_start_date"]), '%Y-%m-%d')
    end_date = datetime.strptime(str(request["form_end_date"]), '%Y-%m-%d')

    if (end_date - start_date).days <= 35:
        request = {"form_city": city,
                   "form_start_date": start_date,
                   "form_end_date": end_date}
        info_from_site = get_weather_from_api(request)

        upload_data_to_base(info_from_site.json())
    elif (end_date - start_date).days > 35:
        request = {"form_city": city,
                   "form_start_date": start_date,
                   "form_end_date": end_date}
        while start_date < (end_date - timedelta(35)):
            request = {"form_city": city,
                       "form_start_date": start_date,
                       "form_end_date": end_date}
            info_from_site = get_weather_from_api(request)
            upload_data_to_base(info_from_site.json())
            start_date += timedelta(35)
        info_from_site = get_weather_from_api(request)
        upload_data_to_base(info_from_site.json())


def preparing_data_to_show(request) -> dict:
    """
    Function collects and accumulates data for placement on web pages
    :param request: POST
    :return: context: dictionary with data to be placed on web pages
    """
    context = {}

    temp_start = datetime
    temp_end = datetime

    city_name = request.POST["form_city"]
    start_date = request.POST["form_start_date"]
    end_date = request.POST["form_end_date"]

    if start_date:
        temp_start = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        temp_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    delta = timedelta(730)
    time_period = temp_end - temp_start

    context['time_period'] = time_period
    context['delta'] = delta

    data_to_show = City.objects.filter(
        city_name__startswith=city_name,
        date__range=(start_date, end_date),
    )

    context["city_name"] = city_name
    context["start_date"] = data_to_show.first().date
    context["end_date"] = data_to_show.last().date

    # 1) temperature characteristics:
    # a) the absolute minimum for the period
    context["min_temp_per_period"] = data_to_show.aggregate(
        Min("min_temp"))["min_temp__min"]
    # b) the average temperature
    context["avg_temp_per_period"] = round(data_to_show.aggregate(
        Avg("avg_temp"))["avg_temp__avg"], 1)
    # c) the absolute maximum for the period
    context["max_temp_per_period"] = data_to_show.aggregate(
        Max("max_temp"))["max_temp__max"]

    # d) if the period is more than 2 years:
    # i) average maximum by the years
    context["years_avg_min"] = data_to_show.values("date_year").annotate(
        Avg("min_temp")).order_by("date_year")
    # ii) average minimum by the years
    context["years_avg_max"] = data_to_show.values("date_year").annotate(
        Avg("max_temp")).order_by("date_year")

    # 2) Precipitation information:
    # a) the number of days with and without precipitation
    #    for the period (in percents)
    days_without_precipitation = data_to_show.annotate(
        Count("precip_mm")).filter(precip_mm=0).count()
    context["percent_days_of_precipitation"] = 100 - round(
        days_without_precipitation /
        data_to_show.annotate(days=Count("precip_mm")).count() * 100)
    # b) two most common types of precipitation for the  period
    context["most_common_weather_per_period"] = data_to_show.values(
        "most_common_weather"
    ).annotate(
        count=Count("most_common_weather")).order_by("-count")[:2]

    # 3) Average wind speed and wind direction:
    # a) Average wind
    context["avg_wind_speed"] = round(
        data_to_show.aggregate(Avg("wind_speed"))["wind_speed__avg"])
    # b) Average wind direction:
    wind_directions = [day.wind_direction for day in data_to_show]
    context["avg_wind_direction"] = round(
        find_average_wind_direction(wind_directions))

    return context


def find_most_common_weather(common_weather: List[str]) -> str:
    """
    Function that calculates the most common weather.
    :param common_weather: list of day common weather
    :return: str: most common weather
    """
    accum_dict = defaultdict(int)
    for value in common_weather:
        accum_dict[value] += 1
    result = max(accum_dict.items(), key=lambda x: x[1])

    return result[0]


def find_average_wind_direction(winds:  List[int]) -> int:
    """
    Function that calculates the average wind direction.
    :param winds: list of day wind direction
    :return: int: average wind direction in degrees
    """
    sin_m = []
    cos_m = []
    for direction in range(len(winds)):
        sin_m.append(math.sin(winds[direction]*math.pi/180))
        cos_m.append(math.cos(winds[direction]*math.pi/180))
    atan_rad = math.atan2(sum(sin_m)/len(winds), sum(cos_m)/len(winds))

    return round(atan_rad*180/math.pi)
