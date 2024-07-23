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



