# Discord Status Badge

[![Discord Status](https://img.shields.io/endpoint?url=https://your-app-url.onrender.com/discord-status&style=flat-square)](https://discord.com/users/your-discord-id)

This project creates a dynamic badge that displays your Discord activity status in your GitHub README.

## Features
- Real-time Discord status updates
- Beautiful flat-square style badge
- Updates every 5 seconds
- Shows Online/Idle/Do Not Disturb/Offline status

## Setup

1. Create a Discord Bot:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Add a bot to your application
   - Enable these Privileged Gateway Intents:
     - Presence Intent
     - Server Members Intent
     - Message Content Intent
   - Copy the bot token

2. Configure Environment Variables:
   Create a `.env` file with:
   ```
   DISCORD_TOKEN=your_bot_token_here
   DISCORD_USER_ID=your_discord_user_id
   ```

3. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Deployment to Render

1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Add Environment Variables:
     - `DISCORD_TOKEN`
     - `DISCORD_USER_ID`

4. Deploy!

## Usage

Once deployed, add this to your GitHub README.md:
```markdown
[![Discord Status](https://img.shields.io/endpoint?url=https://your-app-url.onrender.com/discord-status&style=flat-square)](https://discord.com/users/your-discord-id)
```

Replace `your-app-url.onrender.com` with your actual Render deployment URL.

## Local Development

Run the application locally:
```bash
python app.py
```

The status badge will be available at `http://localhost:5000/discord-status`
