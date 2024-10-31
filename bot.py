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
import sys
from datetime import datetime

# Add at start of bot.py
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Ensure all paths are absolute
log_file = os.path.join(script_dir, 'bot.log')

# Set up logging
logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import logging

logging.basicConfig(
    filename='bot_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

# File to store subscriber IDs
SUBSCRIBERS_FILE = 'subscribers.json'

# Load existing subscribers from file
def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump([], f)
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save subscribers to file
def save_subscribers():
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(subscribers, f)
    logger.info("Subscribers saved to file")

# Load existing subscribers when starting
subscribers = load_subscribers()

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers()  # Save whenever new subscriber is added
        update.message.reply_text('You have been subscribed to project updates!')
    else:
        update.message.reply_text('You are already subscribed to project updates!')

# Function to send message to all subscribers
def send_message_to_subscribers(message):
    """Send message to all subscribers using bot instance"""
    try:
        for chat_id in subscribers:
            bot_instance.bot.send_message(chat_id=chat_id, text=message)
            time.sleep(0.1)  # Add small delay between messages
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")

class ProjectTracker:
    def __init__(self):
        self.sent_projects_file = os.path.join(os.path.dirname(__file__), 'sent_projects.json')
        self.sent_projects = self.load_sent_projects()

    def load_sent_projects(self):
        try:
            if os.path.exists(self.sent_projects_file):
                with open(self.sent_projects_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.error(f"Error loading sent projects: {e}")
            return set()

    def save_sent_projects(self):
        try:
            with open(self.sent_projects_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.sent_projects), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving sent projects: {e}")

    def is_project_sent(self, project_link):
        return project_link in self.sent_projects

    def add_project(self, project_data):
        project_link = project_data['link']
        if not self.is_project_sent(project_link):
            self.sent_projects.add(project_link)
            self.save_sent_projects()
            return True
        return False

def main():
    try:
        tracker = ProjectTracker()
        new_projects_found = False

        # تعيين التوكن مباشرة هنا
        token = '7653393696:AAE53XMbnH8c_10JGcoEg235uHLRPos0tbQ'
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
            project_data = {
                "name": project_name[i],
                "description": project_description[i],
                "budget": project_budget[i],
                "duration": project_duration[i],
                "offers": project_offers[i],
                "average_offers": average_offers[i],
                "link": sub_links[i]
            }

            if tracker.add_project(project_data):
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
                new_projects_found = True

        if not new_projects_found:
            send_message_to_subscribers("لا توجد مشاريع جديدة في الوقت الحالي")

        # Wait to ensure messages are sent
        time.sleep(5)

        # Stop the bot gracefully using bot_instance
        bot_instance.stop()

    except Exception as e:
        logger.error(f"Error initializing bot: {str(e)}")
        bot_instance.stop()  # Ensure cleanup on error
        raise

    logging.info('Bot started')

if __name__ == '__main__':
    main()
