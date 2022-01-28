from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('weather.urls')),
    path('admin/', admin.site.urls),
]

handler400 = "weather.views.handler400"
handler404 = "weather.views.handler404"
handler500 = "weather.views.handler500"
