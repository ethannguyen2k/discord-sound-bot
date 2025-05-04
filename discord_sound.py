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

# Global variables to store timer settings
MIN_MINUTES = 5
MAX_MINUTES = 8

# Global variables to track state
sound_task = None
last_channel = None
start_time = None
wait_time = None

@bot.event
async def on_ready():
    logger.info(f'Bot is ready! Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    # Only care about our own bot's voice state changes
    if member.id != bot.user.id:
        return
    
    global sound_task, start_time, wait_time
    
    # If we were disconnected and then reconnected
    if before.channel and after.channel and before.channel.id == after.channel.id:
        # This means we disconnected and the library auto-reconnected to the same channel
        logger.info("Auto-reconnect detected. Checking sound task status...")
        
        # Check if our sound task is gone
        if sound_task is None or sound_task.done():
            logger.info("Sound task needs to be restarted after reconnection")
            # Calculate remaining time
            remaining_time = None
            if start_time is not None and wait_time is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining_time = max(0, wait_time - elapsed)
                logger.info(f"Resuming timer with {remaining_time/60:.1f} minutes remaining until next sound")
            
            # Restart the sound task with remaining time
            sound_task = bot.loop.create_task(play_random_sounds(after.channel.guild.voice_client, remaining_time))

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
    global sound_task, last_channel, start_time, wait_time
    if ctx.voice_client is not None:
        if sound_task:
            sound_task.cancel()
            sound_task = None
        last_channel = None
        start_time = None
        wait_time = None
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel and stopped playing sounds.")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def status(ctx):
    """Show current bot status and timer information"""
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.send("I'm not currently connected to a voice channel.")
        return
        
    # Calculate remaining time if available
    if start_time is not None and wait_time is not None:
        elapsed = asyncio.get_event_loop().time() - start_time
        remaining = max(0, wait_time - elapsed)
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        await ctx.send(f"Connected to: {ctx.voice_client.channel.name}\n"
                       f"Next sound in: {minutes}m {seconds}s\n"
                       f"Available sounds: {len(SOUND_FILES)}")
    else:
        await ctx.send(f"Connected to: {ctx.voice_client.channel.name}\n"
                       f"Timer status: Not available\n"
                       f"Available sounds: {len(SOUND_FILES)}")

@bot.command()
async def sounds(ctx):
    """List all available sounds"""
    sound_list = "\n".join([f"{i}: {sound}" for i, sound in enumerate(SOUND_FILES)])
    await ctx.send(f"Available sounds:\n```\n{sound_list}\n```")

@bot.command()
async def timer(ctx, min_minutes: int = None, max_minutes: int = None):
    """
    Change the random timer range (in minutes) for the next sound
    Usage: !timer [min] [max]
    Example: !timer 15 30 (sets timer range to 15-30 minutes)
    """
    global MIN_MINUTES, MAX_MINUTES
    
    # If no arguments, show current settings
    if min_minutes is None or max_minutes is None:
        await ctx.send(f"Current timer range: {MIN_MINUTES}-{MAX_MINUTES} minutes")
        
        # If timer is running, show remaining time
        if start_time is not None and wait_time is not None:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = max(0, wait_time - elapsed)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            await ctx.send(f"Next sound will play in: {minutes}m {seconds}s")
        return
        
    # Validate input
    if min_minutes < 1 or max_minutes < min_minutes:
        await ctx.send("Invalid timer range. Min must be at least 1 and Max must be greater than Min.")
        return
        
    # Update timer settings
    MIN_MINUTES = min_minutes
    MAX_MINUTES = max_minutes
    await ctx.send(f"Timer range updated to {MIN_MINUTES}-{MAX_MINUTES} minutes for the next sound cycle.")

@bot.command()
async def set_timer(ctx, minutes: float = None):
    """
    Set the current timer to a specific number of minutes
    Usage: !set_timer [minutes]
    Example: !set_timer 5 (sets current timer to 5 minutes)
    Example: !set_timer 0.5 (sets current timer to 30 seconds)
    """
    global start_time, wait_time, sound_task
    
    # Check if connected to voice
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.send("I'm not currently connected to a voice channel.")
        return
    
    # If no arguments, show current timer
    if minutes is None:
        if start_time is not None and wait_time is not None:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = max(0, wait_time - elapsed)
            min_remaining = int(remaining // 60)
            sec_remaining = int(remaining % 60)
            await ctx.send(f"Current timer: {min_remaining}m {sec_remaining}s remaining")
        else:
            await ctx.send("No active timer found.")
        return
    
    # Validate input
    if minutes < 0:
        await ctx.send("Timer must be a positive number of minutes.")
        return
    
    # Cancel existing task if it exists
    if sound_task:
        sound_task.cancel()
    
    # Set new timer values
    wait_time = minutes * 60
    start_time = asyncio.get_event_loop().time()
    
    # Start new task with manually set timer
    sound_task = bot.loop.create_task(play_random_sounds(ctx.voice_client, wait_time))
    
    # Format message based on whether it's less than a minute
    if minutes < 1:
        seconds = int(minutes * 60)
        await ctx.send(f"Timer set to {seconds} seconds!")
    else:
        # For longer times, show minutes and seconds if there's a fractional part
        min_part = int(minutes)
        sec_part = int((minutes - min_part) * 60)
        
        if sec_part > 0:
            await ctx.send(f"Timer set to {min_part}m {sec_part}s!")
        else:
            await ctx.send(f"Timer set to {min_part} minutes!")

async def play_random_sounds(voice_client, initial_remaining_time=None):
    """
    Play random sounds at random intervals between MIN_MINUTES and MAX_MINUTES.
    If the bot is disconnected, it will attempt to reconnect and resume playing sounds.
    
    Args:
        voice_client: The voice client to play sounds with
        initial_remaining_time: Optional time remaining from a previous session
    """
    global start_time, wait_time
    remaining_time = initial_remaining_time
    
    try:
        while voice_client.is_connected():
            try:
                if remaining_time is None:
                    # Calculate new random wait time in seconds (30-45 minutes)
                    wait_time = random.randint(MIN_MINUTES * 60, MAX_MINUTES * 60)
                    start_time = asyncio.get_event_loop().time()
                    remaining_time = wait_time
                    logger.info(f"Waiting for {wait_time/60:.1f} minutes before playing sound...")
                else:
                    logger.info(f"Resuming with {remaining_time/60:.1f} minutes remaining before playing sound...")
                
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
                    start_time = None
                    remaining_time = None
                
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                logger.info("Sound playing task was cancelled")
                raise
            except Exception as e:
                # If we get disconnected or have another error during the wait
                logger.error(f"Error in play_random_sounds: {e}")
                # Calculate the remaining time if possible
                if start_time is not None and wait_time is not None:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    remaining_time = max(0, wait_time - elapsed)
                    logger.info(f"Recovered from error. {remaining_time/60:.1f} minutes remaining until next sound")
                # Small delay before retrying
                await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Sound task exiting due to error: {e}")
    finally:
        logger.info("Sound playing task has ended")

# Run the bot with your token
bot.run('YOUR_BOT_TOKEN')  # Replace with your actual bot token