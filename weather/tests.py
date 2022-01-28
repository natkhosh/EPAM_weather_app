from django.test import TestCase, Client

from django.urls import reverse

from weather.util import find_most_common_weather, find_average_wind_direction


class FunctionalTestCase(TestCase):

    def set_up(self):
        """
        set up initial params
        """
        self.client = Client()

    def test_find_most_common_weather(self):
        """
        Testing that function actual calculates the most common weather
        """
        common_weather = ["Partly cloudy", "Sunny", "Sunny"]
        result = find_most_common_weather(common_weather)
        expected_result = "Sunny"
        self.assertEqual(result, expected_result)

    def test_find_average_wind_direction(self):
        """
        Testing that function actual calculates the average wind direction
        """
        wind_direction = [48, 23, -15]
        result = find_average_wind_direction(wind_direction)
        expected_result = 19
        self.assertEqual(result, expected_result)

    def test_response_200_and_used_template_on_main_page(self):
        """
       Testing that we get right response
        """
        url = reverse("main")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main_page.html")

    def test_response_200_and_used_template_on_statistic_page(self):
        """
        Testing that backend render city statistic page
        """
        url = ""
        response = self.client.post(url, kwargs={"city_name": "Omsk",
                                                 "start_date": "2011-01-01",
                                                 "end_date": "2012-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("statistic.html")
