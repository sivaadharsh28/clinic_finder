import pandas as pd
import googlemaps
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import os

def main(BOT_TOKEN) -> Application:
    # Google Maps API key from environment variables
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

    # Load the data
    csv_path = "clinics_with_coordinates.csv"
    clinics_df = pd.read_csv(csv_path, encoding='ISO-8859-1')

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logger = logging.getLogger(__name__)

    # States for conversation handler
    MAIN_MENU, NAME, AGE, OCCUPATION, PHONE, EMAIL, LOCATION = range(7)

    # Google Sheets setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('cloud_access.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("User Data").sheet1

    # Function to save user data to Google Sheets
    def save_to_google_sheets(data):
        sheet.append_row([data['Name'], data['Age'], data['Occupation'], data['Phone'], data['Email']])

    async def start(update: Update, context: CallbackContext) -> int:
        reply_keyboard = [['Request for Info', 'Find Clinic']]
        await update.message.reply_text(
            'Hi! Welcome to the Clinic Finder bot! Please choose an option:',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return MAIN_MENU

    async def main_menu(update: Update, context: CallbackContext) -> int:
        user_choice = update.message.text.strip()
        if user_choice == 'Request for Info':
            return await request_info(update, context)
        elif user_choice == 'Find Clinic':
            return await find_clinic(update, context)
        else:
            await update.message.reply_text('Invalid choice. Please select an option from the menu.')
            return MAIN_MENU

    async def request_info(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text('Sure! Let us get in contact with you, could you first tell us your name?', reply_markup=ReplyKeyboardRemove())
        return NAME

    async def find_clinic(update: Update, context: CallbackContext) -> int:
        await update.message.reply_text('Please send me your postal code to find the nearest clinics.', reply_markup=ReplyKeyboardRemove())
        return LOCATION

    async def get_name(update: Update, context: CallbackContext) -> int:
        name = update.message.text.strip()
        if not name.isalpha():
            await update.message.reply_text('Invalid name. Please enter a valid name.')
            return NAME
        context.user_data['name'] = name
        await update.message.reply_text('Thanks! How old are you?')
        return AGE

    async def get_age(update: Update, context: CallbackContext) -> int:
        age = update.message.text.strip()
        if not age.isdigit() or not (5 <= int(age) <= 120):
            await update.message.reply_text('Invalid. Please enter a valid age.')
            return AGE
        context.user_data['age'] = int(age)
        await update.message.reply_text('Great! What is your occupation?')
        return OCCUPATION

    async def get_occupation(update: Update, context: CallbackContext) -> int:
        occupation = update.message.text.strip()
        if not occupation.isalpha():
            await update.message.reply_text('Invalid occupation. Please enter a valid occupation.')
            return OCCUPATION
        context.user_data['occupation'] = occupation
        await update.message.reply_text('Thanks! Please provide your contact number!')
        return PHONE

    async def get_phone(update: Update, context: CallbackContext) -> int:
        phone = update.message.text.strip()
        if not phone.isdigit() or len(phone) != 8:
            await update.message.reply_text('Invalid phone number. Please enter your 8-digit Singapore phone number.')
            return PHONE
        context.user_data['phone'] = phone
        await update.message.reply_text('Lastly, please provide your email address.')
        return EMAIL

    async def get_email(update: Update, context: CallbackContext) -> int:
        email = update.message.text.strip()
        if '@' not in email or ' ' in email:
            await update.message.reply_text('Invalid email. Please enter a valid email address.')
            return EMAIL
        context.user_data['email'] = email
        user_data = {
            'Name': context.user_data['name'],
            'Age': context.user_data['age'],
            'Occupation': context.user_data['occupation'],
            'Phone': context.user_data['phone'],
            'Email': context.user_data['email']
        }
        save_to_google_sheets(user_data)
        await update.message.reply_text('Thank you for providing your information. Now, please send me your postal code to find the nearest clinics!')
        return LOCATION

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

    async def handle_postal_code(update: Update, context: CallbackContext) -> None:
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

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            OCCUPATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_occupation)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postal_code)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(CommandHandler("request_info", request_info))
    application.add_handler(CommandHandler("find_clinic", find_clinic))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(conv_handler)

    return application
