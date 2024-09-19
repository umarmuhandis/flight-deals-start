from data_manager import DataManager
from flight_search import get_city_code, search_flights_for_cities
from notification_manager import send_whatsapp, send_sms

data_manager = DataManager()
destinations = data_manager.get_destination_data()

for destination in destinations:
    if not destination.get("iataCode", ""):
        city_name = destination["city"]
        iata_code = get_city_code(city_name)
        if iata_code:
            print(f"Found IATA code for {city_name}: {iata_code}")
            data_manager.update_destination_codes(destination["id"], iata_code)
            destination["iataCode"] = iata_code
        else:
            print(f"Could not find IATA code for {city_name}")

filtered_destinations = [destination for destination in destinations if destination.get("iataCode")]

flight_results = search_flights_for_cities(filtered_destinations)

updates = []
price_updates = []
cheap_flights_found = False

for city, data in flight_results.items():
    destination = next((d for d in destinations if d["city"] == city), {})
    current_lowest_price = destination.get("lowestPrice", float("inf"))
    new_lowest_price = data["lowestPrice"]

    if new_lowest_price < current_lowest_price:
        if not cheap_flights_found:
            cheap_flights_found = True
            print("Cheap flights found. Loading...")

        from_date = data.get("outbound_date", "N/A")
        to_date = data.get("inbound_date", "N/A")
        stops = data.get("stops", "N/A")
        update_message = (
            f"Lowest price for {city} has changed from ${current_lowest_price} to ${new_lowest_price}. "
            f"Dubai(DXB) to {city}({data['iataCode']}), from {from_date} to {to_date}, with {stops} stop(s)."
        )
        updates.append(update_message)
        price_updates.append((destination["id"], new_lowest_price))
    else:
        print(f"No update needed for {city}. Current price is still the lowest.")

if updates:
    message = "Lowest Price Alert!\n\n" + "\n\n".join(updates)
    send_whatsapp(message)
    send_sms(message)
    for destination_id, new_price in price_updates:
        data_manager.update_lowest_price(destination_id, new_price)
    print("Google Sheet updated with new lowest prices.")
else:
    print("No price updates to report.")