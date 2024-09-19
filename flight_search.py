import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()


client = Client(
        client_id=os.environ.get("AMADEUS_API_KEY"),
        client_secret=os.environ.get("AMADEUS_API_SECRET"))
    


def get_city_code(city_name):
    try:
        response = client.reference_data.locations.cities.get(
            keyword=city_name)
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


def get_cheapest_flights(destination_city_code, origin_city_code="DXB", is_direct=True):
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        six_months_later = tomorrow + timedelta(days=180)

        response = client.shopping.flight_offers_search.get(
            originLocationCode=origin_city_code,
            destinationLocationCode=destination_city_code,
            departureDate=tomorrow.strftime("%Y-%m-%d"),
            returnDate=six_months_later.strftime("%Y-%m-%d"),
            adults=1,
            max=1,
            nonStop=str(is_direct).lower()  # Set the nonStop parameter
        )

        if response.data:
            cheapest_flight = response.data[0]
            price = cheapest_flight["price"]["total"]
            segments = cheapest_flight["itineraries"][0]["segments"]
            outbound_date = segments[0]["departure"]["at"].split("T")[0]
            inbound_date = cheapest_flight["itineraries"][1]["segments"][0]["departure"]["at"].split("T")[0]
            stops = len(segments) - 1  # Calculate the number of stops

            return float(price), outbound_date, inbound_date, stops
        else:
            print(f"No flights found from {origin_city_code} to {destination_city_code}")
            return None, None, None, None

    except ResponseError as error:
        print(f"An error occurred while searching for flights: {error}")
        return None, None, None, None


def search_flights_for_cities(destination_cities, origin_city_code="DXB"):
    print("Searching for flights...")
    origin_code = "DXB" if origin_city_code == "DXB" else get_city_code(origin_city_code)
    if not origin_code:
        print(f"Could not find IATA code for origin city: {origin_city_code}")
        return {}

    results = {}
    for destination in destination_cities:
        dest_city = destination["city"]
        dest_code = destination["iataCode"] or get_city_code(dest_city)
        if dest_code:
            price, outbound_date, inbound_date, stops = get_cheapest_flights(dest_code, origin_code, is_direct=True)
            if not price:  # If no direct flight is found, search for indirect flights
                price, outbound_date, inbound_date, stops = get_cheapest_flights(dest_code, origin_code, is_direct=False)

            if price:
                results[dest_city] = {
                    "lowestPrice": price,
                    "iataCode": dest_code,
                    "id": destination["id"],
                    "outbound_date": outbound_date,
                    "inbound_date": inbound_date,
                    "stops": stops  # Include number of stops in the results
                }
        else:
            print(f"Missing IATA code for destination city: {dest_city}")

    return results