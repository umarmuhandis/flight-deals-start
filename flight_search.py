import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()


class FlightSearch:
    # This class is responsible for talking to the Flight Search API.
    def __init__(self):
        self.amadeus = Client(
            client_id=os.environ.get("AMADEUS_API_KEY"),
            client_secret=os.environ.get("AMADEUS_API_SECRET"),
        )
        self.origin_city = "Dubai"
        self.default_origin_code = "DXB"  # Dubai International Airport code

    def get_city_code(self, city_name):
        try:
            response = self.amadeus.reference_data.locations.cities.get(
                keyword=city_name
            )
            if response.data:
                for city in response.data:
                    if city["name"].lower() == city_name.lower():
                        return city["iataCode"]
                print(f"No exact match found for city: {city_name}")
                return None
            else:
                print(f"No data found for city: {city_name}")
                return None
        except ResponseError as error:
            print(f"An error occurred while searching for {city_name}: {error}")
            return None

    def get_cheapest_flights(self, destination_city_code, origin_city_code=None):
        try:
            tomorrow = datetime.now() + timedelta(days=1)
            six_months_later = tomorrow + timedelta(days=180)

            if origin_city_code is None:
                origin_city_code = self.default_origin_code

            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin_city_code,
                destinationLocationCode=destination_city_code,
                departureDate=tomorrow.strftime("%Y-%m-%d"),
                returnDate=six_months_later.strftime("%Y-%m-%d"),
                adults=1,
                max=1,
            )

            if response.data:
                cheapest_flight = response.data[0]
                price = cheapest_flight["price"]["total"]
                outbound_date = cheapest_flight["itineraries"][0]["segments"][0][
                    "departure"
                ]["at"].split("T")[0]
                inbound_date = cheapest_flight["itineraries"][1]["segments"][0][
                    "departure"
                ]["at"].split("T")[0]
                return float(price), outbound_date, inbound_date
            else:
                print(
                    f"No flights found from {origin_city_code} to {destination_city_code}"
                )
                return None, None, None

        except ResponseError as error:
            print(f"An error occurred while searching for flights: {error}")
            return None, None, None

    def search_flights_for_cities(self, destination_cities, origin_city_code=None):
        if origin_city_code is None:
            origin_code = self.default_origin_code
        else:
            origin_code = self.get_city_code(origin_city_code)
            if not origin_code:
                print(f"Could not find IATA code for origin city: {origin_city_code}")
                return {}

        results = {}
        for destination in destination_cities:
            dest_city = destination["city"]
            dest_code = destination["iataCode"] or self.get_city_code(dest_city)
            if dest_code:
                price, outbound_date, inbound_date = self.get_cheapest_flights(
                    dest_code, origin_code
                )
                if price:
                    results[dest_city] = {
                        "lowestPrice": price,
                        "iataCode": dest_code,
                        "id": destination["id"],
                        "outbound_date": outbound_date,
                        "inbound_date": inbound_date,
                    }
            else:
                print(f"Missing IATA code for destination city: {dest_city}")

        return results
