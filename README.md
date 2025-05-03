# Discord Sound Bot

A simple Discord bot that joins voice channels and plays random sound files at random intervals.

## Features

- Automatically joins voice channels when commanded
- Plays random sound effects at random intervals (30-45 minutes)
- Easy to configure with your own sound files

## Requirements

- Python 3.8 or higher
- discord.py library
- FFmpeg installed on your system and accessible in PATH

## Installation

1. Clone this repository or download the `discord_sound.py` file
2. Install the required Python dependencies:
   ```
   pip install discord.py[voice] pynacl
   ```
3. Install FFmpeg:
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

4. Place your sound files in the same directory as the script
5. Update the `SOUND_FILES` list in the script with your sound file names
6. Replace `'YOUR_BOT_TOKEN'` with your actual Discord bot token

## Creating a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under the token section, click "Copy" to copy your bot token
5. Enable the following Privileged Gateway Intents: Message Content Intent

## Adding the Bot to Your Server

1. In the Discord Developer Portal, go to the "OAuth2" tab
2. In the "URL Generator" section, select the following scopes:
   - bot
3. Select the following bot permissions:
   - Connect
   - Speak
   - Send Messages
   - Read Message History
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

## Usage

1. Run the bot with:
   ```
   python discord_sound.py
   ```
2. In your Discord server, use the following commands:

### Commands

- `!join` - Makes the bot join your current voice channel and start playing random sounds
- `!leave` - Makes the bot leave the voice channel and stop playing sounds

## Customization

You can customize the bot by modifying the following variables in the code:

- `SOUND_FILES` - List of sound files to play
- Random interval timing (currently set to 30-45 minutes)
- Or anything more to your heart desires.