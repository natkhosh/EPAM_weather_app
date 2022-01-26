from django.db import models


class City(models.Model):
    """
    Model defining the structure of weather archive storage.
    """
    id = models.CharField(primary_key=True, max_length=100)
    city_name = models.CharField("City name", max_length=100)
    date = models.DateField()
    date_year = models.IntegerField(verbose_name="weather year")

    min_temp = models.FloatField(null=True)
    avg_temp = models.FloatField(null=True)
    max_temp = models.FloatField(null=True)

    precip_mm = models.FloatField(blank=True, null=True)
    most_common_weather = models.CharField(max_length=100)

    wind_speed = models.FloatField(blank=True, null=True)
    wind_direction = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.city
