import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import json
import time
import telegram
import logging
import atexit

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logging.INFO)
logger = logging.getLogger(__name__)

class BotInstance:
    def __init__(self):
        self.updater = None
        self.bot = None
        
    def stop(self):
        if self.updater:
            self.updater.stop()
            self.updater.is_idle = False
            self.updater.dispatcher.stop()
            self.updater.job_queue.stop()
            logger.info("Bot stopped gracefully")

bot_instance = BotInstance()

def cleanup():
    bot_instance.stop()

atexit.register(cleanup)

def get_bot_token():
    """Get bot token from environment variable"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("No token found! Please set the TELEGRAM_TOKEN environment variable")
    return token

# File to store subscriber IDs
SUBSCRIBERS_FILE = 'subscribers.json'

# Load existing subscribers from file
def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save subscribers to file
def save_subscribers():
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(subscribers, f)

# Load existing subscribers when starting
subscribers = load_subscribers()

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers()  # Save whenever new subscriber is added
        update.message.reply_text('You have been subscribed to project updates!')

# Function to send message to all subscribers
def send_message_to_subscribers(message):
    for chat_id in subscribers:
        Bot.send_message(chat_id=chat_id, text=message)

def main():
    try:
        token = os.getenv('TELEGRAM_TOKEN')
        if not token:
            raise ValueError("No token found!")
            
        bot_instance.updater = Updater(token=token, use_context=True)
        bot_instance.bot = bot_instance.updater.bot
        
        # Set up the Updater and Dispatcher
        dispatcher = bot_instance.updater.dispatcher

        # Add the /start command handler
        start_handler = CommandHandler('start', start)
        dispatcher.add_handler(start_handler)

        # Start the bot
        bot_instance.updater.start_polling()

        # Your existing scraping code
        main_url = 'https://mostaql.com/projects'
        headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
        main_response = requests.get(main_url, headers=headers)
        main_soup = BeautifulSoup(main_response.content, 'html.parser')

        h2_text, sub_links = [], []
        h2_content = main_soup.find_all("h2", {"class": "mrg--bt-reset"})
        for h2 in h2_content:
            h2_text.append(h2.text.strip())
            sub_links.append(h2.a['href'])

        project_name, project_description, project_duration, project_budget, average_offers, project_offers = [], [], [], [], [], []
        for link in sub_links:
            sub_response = requests.get(link, headers=headers).content
            sub_soup = BeautifulSoup(sub_response, 'html.parser')
            # اسم المشروع
            h1_content = sub_soup.find('h1')
            project_name.append(h1_content.text.strip())
            # وصف المشروع
            description = sub_soup.select_one("#project-brief-panel")
            project_description.append(description.text.replace('\n', '').strip())
            # ميزانية المشروع
            budget = sub_soup.select_one("div.hidden-sm > div:nth-child(2) > div:nth-child(1) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(3) > td:nth-child(2)")
            project_budget.append(budget.text.replace('\n', '').strip())
            # مدة تنفيذ المشروع
            duration = sub_soup.select_one("div.hidden-sm > div:nth-child(2) > div:nth-child(1) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(4) > td:nth-child(2)")
            project_duration.append(duration.text.replace('\n', '').strip())
            # عدد العروض المقدمة لهذا المشروع
            offers = sub_soup.select_one("div.hidden-sm > div:nth-child(2) > div:nth-child(1) > table:nth-child(1) > tbody:nth-child(2) > tr:nth-child(6) > td:nth-child(2)")
            project_offers.append(offers.text.replace('\n', '').strip())
            # متوسط سعر العروض المقدمة لهذا المشروع
            average = sub_soup.select_one("#project-meta-panel > div:nth-child(1) > table > tbody > tr:nth-child(5) > td:nth-child(2) > span")
            average_offers.append(average.text.replace('\n', '').strip())

        # Create and send messages for all projects
        for i in range(len(project_name)):
            message = (
                f"اسم المشروع: {project_name[i]}\n"
                f"وصف المشروع: {project_description[i]}\n"
                f"ميزانية المشروع: {project_budget[i]}\n"
                f"مدة المشروع: {project_duration[i]}\n"
                f"عدد العروض: {project_offers[i]}\n"
                f"متوسط سعر العروض: {average_offers[i]}\n"
                f"الرابط: {sub_links[i]}"
            )
            send_message_to_subscribers(message)

        # Wait to ensure messages are sent
        time.sleep(5)

        # Stop the bot gracefully
        bot_instance.updater.idle()
        
    except telegram.error.Conflict:
        logger.error("Another bot instance is running. Shutting down.")
        cleanup()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        cleanup()
        raise

if __name__ == '__main__':
    main()
