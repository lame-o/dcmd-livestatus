from flask import Flask, jsonify
import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv
import logging
import asyncio
import threading
import nest_asyncio
import redis
import json

# Enable nested event loops
nest_asyncio.apply()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
USER_ID = int(os.getenv('DISCORD_USER_ID'))
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Initialize Redis
redis_client = redis.from_url(REDIS_URL)

# Default status
DEFAULT_STATUS = {
    "status": "Offline",
    "color": "gray"
}

def get_current_status():
    try:
        status = redis_client.get('discord_status')
        if status:
            return json.loads(status)
        return DEFAULT_STATUS
    except Exception as e:
        logger.error(f"Error getting status from Redis: {str(e)}")
        return DEFAULT_STATUS

def set_current_status(status):
    try:
        redis_client.set('discord_status', json.dumps(status))
    except Exception as e:
        logger.error(f"Error setting status in Redis: {str(e)}")

class DiscordBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(intents=intents)
        self.target_user_id = USER_ID
        self._loop = None
        
    async def setup_hook(self):
        self.check_presence.start()

    async def on_ready(self):
        logger.info(f'Bot connected as {self.user}')
        await self.check_presence()
        
    async def on_presence_update(self, before, after):
        if before.id == self.target_user_id:
            logger.info(f"Presence update detected: {before.status} -> {after.status}")
            await self.update_status(after)

    @tasks.loop(seconds=10)
    async def check_presence(self):
        try:
            for guild in self.guilds:
                member = guild.get_member(self.target_user_id)
                if member:
                    await self.update_status(member)
                    break
        except Exception as e:
            logger.error(f"Error checking presence: {str(e)}")
            
    async def update_status(self, member):
        try:
            logger.info(f"Updating status for {member.name}: {member.status}")
            
            new_status = {}
            if member.status == discord.Status.online:
                new_status = {"status": "Online", "color": "brightgreen"}
            elif member.status == discord.Status.idle:
                new_status = {"status": "Idle", "color": "yellow"}
            elif member.status == discord.Status.dnd:
                new_status = {"status": "Do Not Disturb", "color": "red"}
            else:
                new_status = {"status": "Offline", "color": "gray"}
            
            set_current_status(new_status)
            logger.info(f"Status updated to: {new_status}")
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")

# Create a single event loop to be shared
event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)

# Initialize the Discord bot
bot = DiscordBot()

def run_bot():
    try:
        event_loop.run_until_complete(bot.start(DISCORD_TOKEN))
    except KeyboardInterrupt:
        event_loop.run_until_complete(bot.close())
    finally:
        event_loop.close()

# Start the bot in a separate thread
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

@app.route("/discord-status")
def get_status():
    try:
        current_status = get_current_status()
        logger.info(f"Serving status: {current_status}")
        
        badge_data = {
            "schemaVersion": 1,
            "label": "Discord",
            "message": current_status["status"],
            "color": current_status["color"],
            "isError": False,
            "namedLogo": "discord",
            "logoColor": "white",
            "style": "flat-square"
        }
    except Exception as e:
        logger.error(f"Error generating badge: {str(e)}")
        badge_data = {
            "schemaVersion": 1,
            "label": "Discord",
            "message": "Offline",
            "color": "gray",
            "isError": False,
            "namedLogo": "discord",
            "logoColor": "white",
            "style": "flat-square"
        }

    response = jsonify(badge_data)
    response.headers.update({
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    })
    return response

@app.route("/refresh")
def refresh():
    try:
        current_status = get_current_status()
        return jsonify({"status": "success", "current_status": current_status})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.after_request
def after_request(response):
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET'
    })
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
