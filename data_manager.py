import requests
import os


class DataManager:
    def __init__(self):
        self.sheety_endpoint = os.environ.get("SHEETY_ENDPOINT")

    def get_destination_data(self):
        response = requests.get(url=self.sheety_endpoint)
        response.raise_for_status()
        data = response.json()
        return data["prices"]

    def update_destination_codes(self, id, iata_code):
        body = {"price": {"iataCode": iata_code}}
        response = requests.put(url=f"{self.sheety_endpoint}/{id}", json=body)
        response.raise_for_status()

    def update_lowest_price(self, id, lowest_price):
        body = {"price": {"lowestPrice": lowest_price}}
        response = requests.put(url=f"{self.sheety_endpoint}/{id}", json=body)
        response.raise_for_status()
