from django import forms


class CityForm(forms.Form):
    city_choices = (
        ("Saint Petersburg", "Saint Petersburg"),
        ("Moscow", "Moscow"),
        ("Tula", "Tula"),
        ("Ufa", "Ufa"),
        ("Omsk", "Omsk"),
        ("Kazan", "Kazan"),
        ("Murmansk", "Murmansk"),
        ("Samara", "Samara"),
        ("Krasnodar", "Krasnodar"),
        ("Yekaterinburg", "Yekaterinburg"),
        ("London", "London"),
        ("Rome", "Rome"),
        ("Paris", "Paris"),
        ("Berlin", "Berlin"),
        ("Tokyo", "Tokyo"),
    )

    form_city = forms.ChoiceField(
        label='City',
        choices=city_choices,
        initial='',
        widget=forms.Select(),
        required=True)


class StartDateForm(forms.Form):
    form_start_date = forms.DateField(
        label="Start date",
        required=True,
        help_text="format: YYYY-MM-DD")


class EndDateForm(forms.Form):
    form_end_date = forms.DateField(
        label="End date",
        required=True,
        help_text="format: YYYY-MM-DD")
