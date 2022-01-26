from django.urls import path
from . import views



urlpatterns = [
    path('', views.get_data, name="main"),
    path('statistic', views.city, name="statistic"),
]