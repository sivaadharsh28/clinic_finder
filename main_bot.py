import os
import pandas as pd
import googlemaps
import logging
import json
import gzip
from geopy.distance import geodesic
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler

BOT_KEY = os.getenv('API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Load the data
csv_path = "clinics_with_coordinates.csv"
clinics_df = pd.read_csv(csv_path, encoding='ISO-8859-1')

# Load the postal codes JSON file with gzip handling
postal_codes_data = []
try:
    with gzip.open('singpostcode.json.gz', 'rt', encoding='utf-8') as f:
        postal_codes_data = json.load(f)
except UnicodeDecodeError as e:
    print("Error loading JSON file with UTF-8 encoding. Trying with 'ISO-8859-1' encoding.")
    try:
        with gzip.open('singpostcode.json.gz', 'rt', encoding='ISO-8859-1') as f:
            postal_codes_data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON file: {e}")
        exit(1)

postal_codes_dict = {entry["POSTAL"]: entry for entry in postal_codes_data}

# Initialize Google Maps client (for place ID retrieval)
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# List of authorised usernames
AUTHORIZED_USERNAMES = ["fill in username"]  

LOCATION = range(1)

# Enabling logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def is_authorized(username):
    return username in AUTHORIZED_USERNAMES

async def is_authorized_user_in_group(chat):
    administrators = await chat.get_administrators()
    logger.info(f"Administrators in group: {[admin.user.username for admin in administrators]}")
    for member in administrators:
        if member.user.username in AUTHORIZED_USERNAMES:
            return True
    return False

async def start(update: Update, context: CallbackContext) -> int:
    username = update.message.from_user.username
    chat_type = update.message.chat.type

    logger.info(f"Chat type: {chat_type}, Username: {username}")

    if chat_type == 'private' and not is_authorized(username):
        await update.message.reply_text('You are not authorized to use this bot.')
        return ConversationHandler.END

    if chat_type in ['group', 'supergroup'] and not await is_authorized_user_in_group(update.message.chat):
        await update.message.reply_text('No authorized user in the group to use this bot.')
        return ConversationHandler.END

    await update.message.reply_text(
        'Hi! Welcome to the Clinic Finder bot! Please send me your postal code to find the nearest clinics.',
        reply_markup=ReplyKeyboardRemove()
    )
    return LOCATION

def get_coordinates_from_postal_code(postal_code):
    # Look up the postal code in the JSON data
    if postal_code in postal_codes_dict:
        entry = postal_codes_dict[postal_code]
        return float(entry["LATITUDE"]), float(entry["LONGITUDE"])
    else:
        return None

def find_nearest_clinics(postal_code, clinics_df, n=5):
    user_coords = get_coordinates_from_postal_code(postal_code)
    if not user_coords:
        return "Invalid postal code"

    # Calculate distances using geopy
    clinics_df['Distance'] = clinics_df.apply(lambda row: geodesic(user_coords, (row['Latitude'], row['Longitude'])).meters, axis=1)
    nearest_clinics = clinics_df.nsmallest(n, 'Distance')

    nearest_clinics['Place_ID'] = nearest_clinics.apply(lambda row: get_place_id(row['Clinic Name'], row['Address']), axis=1)

    return nearest_clinics[['Clinic Name', 'Address', 'Latitude', 'Longitude', 'Place_ID']]

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

async def handle_postal_code(update: Update, context: CallbackContext) -> None:
    username = update.message.from_user.username
    chat_type = update.message.chat.type

    logger.info(f"Chat type: {chat_type}, Username: {username}")
    
    if chat_type == 'private' and not is_authorized(username):
        await update.message.reply_text('You are not authorized to use this bot.')
        return

    if chat_type in ['group', 'supergroup'] and not await is_authorized_user_in_group(update.message.chat):
        await update.message.reply_text('No authorized user in the group to use this bot.')
        return

    postal_code = update.message.text.strip()
    
    if not postal_code.isdigit() or len(postal_code) != 6:
        await update.message.reply_text("Invalid postal code. Please enter a 6-digit postal code.")
        return

    logger.info(f"Received postal code: {postal_code}")
    nearest_clinics = find_nearest_clinics(postal_code, clinics_df)
    if isinstance(nearest_clinics, str):
        logger.info(f"Response: {nearest_clinics}")
        await update.message.reply_text(nearest_clinics)
    else:
        response = "\n\n".join([f"{row['Clinic Name']} : {row['Address']} \n[Google Maps]({get_google_maps_url(row['Clinic Name'], row['Address'])})" for i, row in nearest_clinics.iterrows()])
        logger.info(f"Response: {response}")
        await update.message.reply_text(response, parse_mode='Markdown')

def get_google_maps_url(clinic_name, clinic_address):
    return f"https://www.google.com/maps/search/?api=1&query={clinic_name},{clinic_address},Singapore"

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a postal code, and I will find the nearest clinics for you.')

def main():
    application = ApplicationBuilder().token(BOT_KEY).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postal_code)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    from app import keep_alive
    keep_alive()
    main()
