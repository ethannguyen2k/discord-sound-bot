import discord
import asyncio
import random
import os
from discord.ext import commands

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

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')

@bot.command()
async def join(ctx):
    """Join the voice channel and start playing sounds randomly"""
    if ctx.author.voice is None:
        await ctx.send("You are not in a voice channel!")
        return
    
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()
    
    await ctx.send(f"Joined {voice_channel.name} and will play random sounds at random intervals!")
    
    # Start the random sound player
    bot.loop.create_task(play_random_sounds(ctx.voice_client))

@bot.command()
async def leave(ctx):
    """Leave the voice channel and stop playing sounds"""
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel and stopped playing sounds.")
    else:
        await ctx.send("I'm not in a voice channel!")

async def play_random_sounds(voice_client):
    """Play random sounds at random intervals between 30-45 minutes"""
    while voice_client.is_connected():
        # Calculate random wait time in seconds (30-45 minutes)
        wait_time = random.randint(30 * 60, 45 * 60)
        
        # Wait for the random time
        print(f"Waiting for {wait_time/60:.1f} minutes before playing sound...")
        await asyncio.sleep(wait_time)
        
        # Play the sound if still connected
        if voice_client.is_connected():
            # Select a random sound file from the list
            selected_sound = random.choice(SOUND_FILES)
            print(f"Playing sound: {selected_sound}")
            
            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(executable="ffmpeg", source=selected_sound)
            
            # Play the sound
            voice_client.play(audio_source)
            
            # Wait until the sound is finished playing
            while voice_client.is_playing():
                await asyncio.sleep(1)

# Run the bot with your token
bot.run('YOUR_BOT_TOKEN')  # Replace with your actual bot token