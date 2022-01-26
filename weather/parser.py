import math
import os
from collections import defaultdict
import requests
from django.db.models import Max, Min, Avg, Count
from .models import City
from datetime import datetime, timedelta


def checking_city_in_database(city_name):
    """The function checks information about the requested
    city in the database"""
    return City.objects.filter(city_name__startswith=city_name).values()


def weather_data(request):
    """The function getting request from client (requested city)
        and collecting information in the next algorithm
        1) Checking city in database. If the city is in the database - the
         function checks relevance weather information. If not - getting
          repeated request;
        2) If the city isn't in database - function getting request;
        3) If information about the requested city is relevant in the
         database - client would get the weather from the database.
        """
    requested_city = request["form_city"]
    city_check = checking_city_in_database(requested_city)
    requested_date = datetime.strptime(request["form_end_date"],
                                       '%Y-%m-%d').date()

    if not city_check:
        initial_download(request)

        # return render(request, "checker/city.html", result_dict)
        print("Данные обновлены!")

    if requested_date > City.objects.filter(
            city_name__startswith=requested_city).last().date:

        request_upd = {
            "form_city": requested_city,
            "form_start_date": City.objects.filter(
                city_name__startswith=requested_city).last().date,
            "form_end_date": request["form_end_date"]}

        initial_download(request_upd)


def get_weather_from_api(request_data: dict):
    link = "https://api.worldweatheronline.com/premium/v1/past-weather.ashx"
    #secret_key = 'de04e16261d442a18b2214346222201'
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


def upload_data_to_base(data: dict):
    city_name = data["data"]["request"][0]["query"]
    for date in data["data"]["weather"]:

        hourly = date["hourly"]
        day_record = City()
        day_record.id = f'{str(date["date"])}-{city_name}'
        day_record.city_name = city_name
        day_record.date = str(date["date"])

        day_record.date_year = str(date["date"][:4])
        # day_record.date_month = str(date["date"][5:7])
        # day_record.date_day = str(date["date"][8:])

        day_record.avg_temp = date["avgtempC"]
        day_record.max_temp = date["maxtempC"]
        day_record.min_temp = date["mintempC"]

        day_record.precip_mm = sum([float(time["precipMM"])
                                    for time in hourly]) / len(hourly)

        day_record.most_common_weather = find_most_common_weather(
            [time["weatherDesc"][0]["value"] for time in hourly])

        day_record.wind_direction = calculate_average_wind_direction(
            [int(time["winddirDegree"]) for time in hourly])

        day_record.wind_speed = sum(
            [int(time["windspeedKmph"]) for time in hourly]) / len(hourly)

        day_record.save()


def initial_download(request):
    city = request["form_city"]

    sd = str(request["form_start_date"])
    ed = str(request["form_end_date"])
    startdate = datetime.strptime(sd, '%Y-%m-%d')
    enddate = datetime.strptime(ed, '%Y-%m-%d')

    print(type(startdate))
    if (enddate - startdate).days <= 35:
        request = {"form_city": city,
                   "form_start_date": startdate,
                   "form_end_date": enddate}
        info_from_site = get_weather_from_api(request)
        upload_data_to_base(info_from_site.json())
    elif (enddate - startdate).days > 35:
        request = {"form_city": city,
                   "form_start_date": startdate,
                   "form_end_date": enddate}
        while startdate < (enddate - timedelta(35)):
            request = {"form_city": city,
                       "form_start_date": startdate,
                       "form_end_date": enddate}
            info_from_site = get_weather_from_api(request)
            upload_data_to_base(info_from_site.json())
            startdate += timedelta(35)
        info_from_site = get_weather_from_api(request)
        upload_data_to_base(info_from_site.json())


def data_calculation(request):
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
    # days_period = time_period.days + 1

    context['time_period'] = time_period
    context['delta'] = delta

    data_to_show = City.objects.filter(
        city_name__startswith=city_name,
        date__range=(start_date, end_date),
    )

    context["city_name"] = city_name
    context["start_date"] = data_to_show.first().date
    context["end_date"] = data_to_show.last().date

    context["min_temp_per_period"] = data_to_show.aggregate(
        Min("min_temp"))["min_temp__min"]

    context["avg_temp_per_period"] = round(data_to_show.aggregate(
        Avg("avg_temp"))["avg_temp__avg"], 1)

    context["max_temp_per_period"] = data_to_show.aggregate(
        Max("max_temp"))["max_temp__max"]

    context["years_avg_min"] = data_to_show.values("date_year").annotate(
        Avg("min_temp")).order_by("date_year")

    context["years_avg_max"] = data_to_show.values("date_year").annotate(
        Avg("max_temp")).order_by("date_year")

    days_without_precipitation = data_to_show.annotate(
        Count("precip_mm")).filter(precip_mm=0).count()

    context["percent_days_of_precipitation"] = 100 - round(
        days_without_precipitation /
        data_to_show.annotate(days=Count("precip_mm")).count() * 100)

    # print(days_without_precipitation, context["percent_days_of_precipitation"])

    context["most_common_weather_per_period"] = data_to_show.values(
        "most_common_weather"
    ).annotate(
        count=Count("most_common_weather")).order_by("-count")[:2]

    context["avg_wind_speed"] = round(
        data_to_show.aggregate(
            Avg("wind_speed"
                )
        )["wind_speed__avg"])
    wind_directions = [day.wind_direction for day in data_to_show]
    context["avg_wind_direction_1"] = [day.wind_direction for day
                                       in data_to_show]

    context["avg_wind_direction"] = round(
        calculate_average_wind_direction(wind_directions)
    )

    return context


def find_most_common_weather(descriptions):
    d = defaultdict(int)
    for value in descriptions:
        d[value] += 1
    result, _ = max(d.items(), key=lambda x: x[1])
    return result


def calculate_average_wind_direction(winds: list):
    sin_m = []
    cos_m = []
    for i in range(len(winds)):
        sin_m.append(math.sin(winds[i]*math.pi/180))
        cos_m.append(math.cos(winds[i]*math.pi/180))
    atan_rad = math.atan2(sum(sin_m)/len(winds), sum(cos_m)/len(winds))
    return round(atan_rad*180/math.pi)
