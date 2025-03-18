**Clinic Finder Bot**    
A powerful and user-friendly bot designed to help users locate clinics based on their location. This bot was made for a insurance company to allow clients to easily locate the nearest approved Traditional Chinese Medicine Clinics. 

**Features**  
🌍 Location-Based Search: Finds clinics near the user's postal code  
🧭 Integration with Maps: Offers directions to the selected clinic via Google Maps or other navigation tools.  
🔒 Access Control: The bot can only be used directly and added into groups by approved users. Others can only use the bot in groups with the approved users.  

**How It Works**  
User Input: The bot takes the user’s postal code
Data Processing: It fetches clinic information from a predefined database 
Results Display: The bot presents a list of the nearest 5 clinics matching the user’s criteria, along with details like address and contact.
Navigation Assistance: Upon selection, the bot provides navigation assistance to the chosen clinic.

**Installation Instructions**   
Clone the repository  
Install dependencies from requirements.txt  
Create a file named config.json in the root directory and add your Google API Key  
Add your predefined data as a csv file to your directory  
Add your Telegram bot API key and approved users telegram handles in the relevant sections in the main_bot.py code  
Run the main_bot.py file to start the bot  

**Technologies Used**  
Python: Core programming language for bot logic.
Google Maps API: For geolocation, navigation, and mapping services.
Flask: For backend integration 
