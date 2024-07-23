import googlemaps
import pandas as pd
import time

# Initialize the client
gmaps = googlemaps.Client(key='AIzaSyC8YolHfAp5MwC9Sl0mq-Q-oKzqhYp3kyY')

# Load the updated CSV file
csv_path = r"C:\Users\Siva Adharsh\Clinic Address\clinics_with_addresses.csv"
clinics_df = pd.read_csv(csv_path, encoding='ISO-8859-1')

# Function to get coordinates from address using Google Maps API
def get_coordinates(address):
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return (None, None)
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
        return (None, None)

# Fetch coordinates for each address
clinics_df['Coordinates'] = clinics_df['Address'].apply(get_coordinates)
clinics_df[['Latitude', 'Longitude']] = pd.DataFrame(clinics_df['Coordinates'].tolist(), index=clinics_df.index)

# Drop rows with missing coordinates
clinics_df.dropna(subset=['Latitude', 'Longitude'], inplace=True)

# Save the updated data with coordinates
try:
    clinics_df.to_csv(r"C:\Users\Siva Adharsh\Downloads\clinics_with_coordinates.csv", index=False)
except PermissionError:
    print("Permission error: Could not write to the file. Please close the file if it is open and ensure you have write permissions.")
