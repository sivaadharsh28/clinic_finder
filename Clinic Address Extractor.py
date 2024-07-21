import googlemaps
import pandas as pd
import time

# Initialize the client
gmaps = googlemaps.Client(key='AIzaSyC8YolHfAp5MwC9Sl0mq-Q-oKzqhYp3kyY')

# Load the CSV file
csv_path = r"C:\Users\Siva Adharsh\Downloads\Recommended-List-as-at-28-May-2024.csv"
clinics_df = pd.read_csv(csv_path)

# Ensure the column 'Clinic Name' is treated as strings and handle NaNs
clinics_df['Clinic Name'] = clinics_df['Clinic Name'].astype(str).fillna('')

# Function to get address from clinic name
def get_address(clinic_name):
    if clinic_name.strip() == '':
        return None
    try:
        geocode_result = gmaps.geocode(clinic_name + ", Singapore")
        if geocode_result:
            return geocode_result[0]['formatted_address']
        else:
            return None
    except Exception as e:
        print(e)
        return None

# Fetch addresses for each clinic
clinics_df['Address'] = clinics_df['Clinic Name'].apply(get_address)

# Save the updated data
clinics_df.to_csv("clinics_with_addresses.csv", index=False)





from geopy.geocoders import Nominatim
import pandas as pd

# Initialize the geocoder
geolocator = Nominatim(user_agent="clinic_locator")

# Load the updated CSV file
csv_path = r"C:\Users\Siva Adharsh\Clinic Address\clinics_with_addresses.csv"
clinics_df = pd.read_csv(csv_path)

# Function to get coordinates from address
def get_coordinates(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            return (None, None)
    except Exception as e:
        print(e)
        return (None, None)

# Fetch coordinates for each address
clinics_df['Coordinates'] = clinics_df['Address'].apply(get_coordinates)
clinics_df[['Latitude', 'Longitude']] = pd.DataFrame(clinics_df['Coordinates'].tolist(), index=clinics_df.index)

# Drop rows with missing coordinates
clinics_df.dropna(subset=['Latitude', 'Longitude'], inplace=True)

# Save the updated data with coordinates
clinics_df.to_csv("clinics_with_coordinates.csv", index=False)

# Optional: Print the updated dataframe to verify
print(clinics_df)
