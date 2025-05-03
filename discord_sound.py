import discord
import asyncio
import random
import os
import logging
from discord.ext import commands

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sound_bot')

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# List of sound files
SOUND_FILES = [
    'sound_file_1.mp3',  # Replace with your actual file names
    'sound_file_2.mp3',
    'sound_file_3.mp3',
    'sound_file_4.mp3'
]

# Global variables to track state
sound_task = None
last_channel = None

@bot.event
async def on_ready():
    logger.info(f'Bot is ready! Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    # Only care about our own bot's voice state changes
    if member.id != bot.user.id:
        return
    
    # If we were disconnected but we have a last_channel
    if before.channel and not after.channel and last_channel:
        logger.info("Bot was disconnected unexpectedly. Attempting to reconnect...")
        try:
            # Wait a moment before trying to reconnect
            await asyncio.sleep(5)
            voice_client = await last_channel.connect()
            # Restart the sound playing task
            global sound_task
            if sound_task:
                sound_task.cancel()
            sound_task = bot.loop.create_task(play_random_sounds(voice_client))
            logger.info("Successfully reconnected and restarted sound task")
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")

@bot.command()
async def join(ctx):
    """Join the voice channel and start playing sounds randomly"""
    if ctx.author.voice is None:
        await ctx.send("You are not in a voice channel!")
        return
    
    voice_channel = ctx.author.voice.channel
    global last_channel
    last_channel = voice_channel
    
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()
    
    await ctx.send(f"Joined {voice_channel.name} and will play random sounds at random intervals!")
    
    # Start the random sound player
    global sound_task
    if sound_task:
        sound_task.cancel()
    sound_task = bot.loop.create_task(play_random_sounds(ctx.voice_client))

@bot.command()
async def leave(ctx):
    """Leave the voice channel and stop playing sounds"""
    global sound_task, last_channel
    if ctx.voice_client is not None:
        if sound_task:
            sound_task.cancel()
            sound_task = None
        last_channel = None
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel and stopped playing sounds.")
    else:
        await ctx.send("I'm not in a voice channel!")

async def play_random_sounds(voice_client):
    """Play random sounds at random intervals between 30-45 minutes"""
    wait_time = None
    start_time = None
    remaining_time = None
    
    while voice_client.is_connected():
        try:
            if wait_time is None:
                # Calculate new random wait time in seconds (30-45 minutes)
                wait_time = random.randint(30 * 60, 45 * 60)
                start_time = asyncio.get_event_loop().time()
                remaining_time = wait_time
                logger.info(f"Waiting for {wait_time/60:.1f} minutes before playing sound...")
            
            # Wait for the remaining time
            await asyncio.sleep(remaining_time)
            
            # Play the sound if still connected
            if voice_client.is_connected():
                # Select a random sound file from the list
                selected_sound = random.choice(SOUND_FILES)
                logger.info(f"Playing sound: {selected_sound}")
                
                try:
                    # Create FFmpeg audio source
                    audio_source = discord.FFmpegPCMAudio(executable="ffmpeg", source=selected_sound)
                    
                    # Play the sound
                    voice_client.play(audio_source)
                    
                    # Wait until the sound is finished playing
                    while voice_client.is_playing():
                        await asyncio.sleep(1)
                    
                    logger.info(f"Finished playing: {selected_sound}")
                except Exception as e:
                    logger.error(f"Error playing sound: {e}")
                
                # Reset for next interval
                wait_time = None
            
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            logger.info("Sound playing task was cancelled")
            break
        except Exception as e:
            # If we get disconnected or have another error during the wait
            logger.error(f"Error in play_random_sounds: {e}")
            # Calculate the remaining time
            if start_time is not None and wait_time is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining_time = max(0, wait_time - elapsed)
                logger.info(f"Recovered from error. {remaining_time/60:.1f} minutes remaining until next sound")
            else:
                # Reset if we can't calculate remaining time
                wait_time = None
            # Small delay before retrying
            await asyncio.sleep(5)

# Run the bot with your token
bot.run('YOUR_BOT_TOKEN')  # Replace with your actual bot token