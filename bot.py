import telebot
import json
import os
import re

# Load token from environment or config.json
if os.getenv("TELEGRAM_API_TOKEN"):
    API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
else:
    with open('config.json') as config_file:
        config = json.load(config_file)
    API_TOKEN = config['api_token']

bot = telebot.TeleBot(API_TOKEN)

# Temporary storage for bulk contacts
bulk_contacts = {}

# Handle '/start' command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello")

# Handle '/bulk' command
@bot.message_handler(commands=['bulk'])
def bulk_start(message):
    chat_id = message.chat.id
    bulk_contacts[chat_id] = []  # Initialize a list for the user's contacts
    bot.reply_to(message, "Bulk mode activated. Send contacts in the format: Name +Number. Use /saved to finish.")

# Collect messages after '/bulk'
@bot.message_handler(func=lambda message: message.chat.id in bulk_contacts and message.text != '/saved')
def collect_bulk_contacts(message):
    chat_id = message.chat.id
    try:
        # Extract name and number using regex for flexibility
        contact_info = re.match(r"^(.+)\s(\+?\d+)$", message.text.strip())
        if not contact_info:
            bot.reply_to(message, "Please send in the format: Name +Number")
            return

        name, number = contact_info.groups()

        # Store the contact in the bulk list with [RT] prefix
        bulk_contacts[chat_id].append({'name': f"RT {name.upper()}", 'number': number})
        bot.reply_to(message, f"Added: {name.upper()} {number}")

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Handle '/saved' command
@bot.message_handler(commands=['saved'])
def bulk_save(message):
    chat_id = message.chat.id

    # Check if the user has sent any bulk contacts
    if chat_id not in bulk_contacts or len(bulk_contacts[chat_id]) == 0:
        bot.reply_to(message, "No contacts to save. Use /bulk to start adding contacts.")
        return

    try:
        # Create a single .vcf file for all contacts
        vcf_file_path = f"bulk_contacts_{chat_id}.vcf"
        with open(vcf_file_path, "w") as vcf_file:
            # Write all contacts into one .vcf file
            for contact in bulk_contacts[chat_id]:
                vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact['name']}
TEL:{contact['number']}
END:VCARD
"""
                vcf_file.write(vcf_content)

        # Send the generated vCard file to the user
        with open(vcf_file_path, "rb") as vcf_file:
            bot.send_document(chat_id, vcf_file)

        # Remove the .vcf file after sending
        os.remove(vcf_file_path)
        
        # Clear user's bulk contact list after saving
        del bulk_contacts[chat_id]
        bot.reply_to(message, "All contacts have been saved in a single .vcf file and sent.")

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

# Polling the bot to keep it running
if __name__ == '__main__':
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot polling failed: {str(e)}")
