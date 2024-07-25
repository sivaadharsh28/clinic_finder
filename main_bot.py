import os
import telebot
import random
import time
import pandas as pd
import googlemaps
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

API_KEY = os.getenv('API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
bot = telebot.TeleBot(API_KEY)

# Load the data
csv_path = "clinics_with_coordinates.csv"
clinics_df = pd.read_csv(csv_path, encoding='ISO-8859-1')

# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('cloud_access.json', scope)
client = gspread.authorize(creds)
sheet = client.open("User Data").sheet1

# Function to save user data to Google Sheets
def save_to_google_sheets(data):
    sheet.append_row([data['Name'], data['Age'], data['Occupation'], data['Phone'], data['Email']])

# States for conversation handler
MAIN_MENU, NAME, AGE, OCCUPATION, PHONE, EMAIL, LOCATION = range(7)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

@bot.message_handler(commands=['start'])
def greet(message):
    bot.send_message(message.chat.id, "Hi! Welcome to the Clinic Finder bot! Please choose an option: /request_info or /find_clinic")

@bot.message_handler(commands=['request_info'])
def request_info(message):
    msg = bot.reply_to(message, 'Sure! Let us get in contact with you, could you first tell us your name?')
    bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    try:
        name = message.text
        msg = bot.reply_to(message, 'Thanks! How old are you?')
        bot.register_next_step_handler(msg, process_age_step, name)
    except Exception as e:
        bot.reply_to(message, 'ooops')

def process_age_step(message, name):
    try:
        age = int(message.text)
        msg = bot.reply_to(message, 'Great! What is your occupation?')
        bot.register_next_step_handler(msg, process_occupation_step, name, age)
    except Exception as e:
        bot.reply_to(message, 'ooops')

def process_occupation_step(message, name, age):
    try:
        occupation = message.text
        msg = bot.reply_to(message, 'Thanks! Please provide your contact number!')
        bot.register_next_step_handler(msg, process_phone_step, name, age, occupation)
    except Exception as e:
        bot.reply_to(message, 'ooops')

def process_phone_step(message, name, age, occupation):
    try:
        phone = message.text
        msg = bot.reply_to(message, 'Lastly, please provide your email address.')
        bot.register_next_step_handler(msg, process_email_step, name, age, occupation, phone)
    except Exception as e:
        bot.reply_to(message, 'ooops')

def process_email_step(message, name, age, occupation, phone):
    try:
        email = message.text
        user_data = {
            'Name': name,
            'Age': age,
            'Occupation': occupation,
            'Phone': phone,
            'Email': email
        }
        save_to_google_sheets(user_data)
        bot.reply_to(message, 'Thank you for providing your information. Now, please send me your postal code to find the nearest clinics!')
    except Exception as e:
        bot.reply_to(message, 'ooops')

@bot.message_handler(commands=['find_clinic'])
def find_clinic(message):
    msg = bot.reply_to(message, 'Please send me your postal code to find the nearest clinics.')
    bot.register_next_step_handler(msg, process_location_step)

def process_location_step(message):
    try:
        postal_code = message.text
        nearest_clinics = find_nearest_clinics(postal_code, clinics_df)
        if isinstance(nearest_clinics, str):
            bot.reply_to(message, nearest_clinics)
        else:
            response = "\n\n".join([f"{row['Clinic Name']} : {row['Address']} \n[Google Maps]({get_google_maps_url(row['Clinic Name'], row['Address'])})" for i, row in nearest_clinics.iterrows()])
            bot.reply_to(message, response, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, 'ooops')

def find_nearest_clinics(postal_code, clinics_df, n=5):
    user_coords = get_coordinates_from_postal_code(postal_code)
    if not user_coords:
        return "Invalid postal code"

    destinations = clinics_df.apply(lambda row: f"{row['Latitude']},{row['Longitude']}", axis=1).tolist()

    max_batch_size = 25
    batches = [destinations[i:i + max_batch_size] for i in range(0, len(destinations), max_batch_size)]

    all_distances = []

    for batch in batches:
        distances_result = gmaps.distance_matrix(origins=[user_coords], destinations=batch, mode="driving")

        if distances_result['status'] != 'OK':
            print(f"Distance Matrix Error: {distances_result['status']}")
            return "Error in distance matrix request"

        distances = [element['distance']['value'] if element['status'] == 'OK' else float('inf') for element in distances_result['rows'][0]['elements']]
        all_distances.extend(distances)

    clinics_df['Distance'] = all_distances
    nearest_clinics = clinics_df.nsmallest(n, 'Distance')

    nearest_clinics['Place_ID'] = nearest_clinics.apply(lambda row: get_place_id(row['Clinic Name'], row['Address']), axis=1)

    return nearest_clinics[['Clinic Name', 'Address', 'Latitude', 'Longitude', 'Place_ID']]

def get_coordinates_from_postal_code(postal_code):
    try:
        geocode_result = gmaps.geocode(postal_code + ", Singapore")
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return None
    except Exception as e:
        print(f"Error geocoding postal code {postal_code}: {e}")
        return None

def get_place_id(clinic_name, clinic_address):
    try:
        query = f"{clinic_name}, {clinic_address}, Singapore"
        place_result = gmaps.find_place(input=query, input_type="textquery", fields=["place_id"])
        if place_result and place_result['status'] == 'OK':
            place_id = place_result['candidates'][0]['place_id']
            return place_id
        else:
            return None
    except Exception as e:
        print(f"Error getting place_id for clinic {clinic_name} at {clinic_address}: {e}")
        return None

def get_google_maps_url(clinic_name, clinic_address):
    return f"https://www.google.com/maps/search/?api=1&query={clinic_name},{clinic_address},Singapore"

from app import keep_alive
keep_alive()

bot.polling()
