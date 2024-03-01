from settings import SiteSettings
from Apisite.utility.site_api_handler import SiteApiInterface


site = SiteSettings()

url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"

headers = {
    "X-RapidAPI-Key": site.api_key.get_secret_value(),
    "X-RapidAPI-Host": site.host_api
}

params = {
    "types": "CITY",
    "countryIds": "RU",
    "minPopulation": None,
    "maxPopulation": None,
    "namePrefix": None,
    "languageCode": "RU",
    "limit": "1",
    "sort": None
}

site_api = SiteApiInterface()

if __name__ == '__main__':
    site_api()
