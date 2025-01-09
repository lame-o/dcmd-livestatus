from flask import Flask, jsonify
import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv
import logging
import asyncio
from threading import Thread

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
USER_ID = int(os.getenv('DISCORD_USER_ID'))  # Discord IDs should be integers

# Global variable to store current status
current_status = {
    "status": "Offline",
    "color": "red"
}

class DiscordBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.target_user_id = USER_ID
        
    async def setup_hook(self):
        # Start the presence check loop
        self.check_presence.start()

    async def on_ready(self):
        logger.info(f'Bot connected as {self.user}')
        
    @tasks.loop(seconds=5)
    async def check_presence(self):
        try:
            # Get all mutual guilds
            for guild in self.guilds:
                # Get the member object
                member = guild.get_member(self.target_user_id)
                if member:
                    logger.info(f"Found member {member.name} with status {member.status}")
                    
                    # Update the global status
                    if member.status == discord.Status.online:
                        current_status.update({"status": "Online", "color": "brightgreen"})
                    elif member.status == discord.Status.idle:
                        current_status.update({"status": "Idle", "color": "yellow"})
                    elif member.status == discord.Status.dnd:
                        current_status.update({"status": "Do Not Disturb", "color": "red"})
                    else:
                        current_status.update({"status": "Offline", "color": "red"})
                    
                    logger.info(f"Updated status to: {current_status}")
                    return  # Exit after finding the user
                
        except Exception as e:
            logger.error(f"Error checking presence: {str(e)}")

# Initialize the Discord bot
bot = DiscordBot()

def run_bot():
    asyncio.run(bot.start(DISCORD_TOKEN))

# Start the bot in a separate thread
bot_thread = Thread(target=run_bot, daemon=True)
bot_thread.start()

@app.route("/discord-status")
def get_status():
    logger.info(f"Current status: {current_status}")
    response = jsonify({
        "schemaVersion": 1,
        "label": "Discord",
        "message": current_status["status"],
        "color": current_status["color"],
        "style": "flat-square",
        "namedLogo": "discord",
        "cacheSeconds": 5
    })
    response.headers['Content-Type'] = 'application/json'
    return response

# Add CORS support for the badge
@app.after_request
def after_request(response):
    if response.headers.get('Content-Type') == 'application/json':
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True, use_reloader=False)
