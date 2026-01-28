# Созданно BeautiflPanda Размещенно на
import disnake
from disnake.ext import commands
import yt_dlp
import logging
import os
from config import TOKEN
from urllib.parse import urlparse

# --- Logging ---
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    filename="logs.log",
)

queue = []
queue_counter = 1
current_title = None

bot = commands.Bot(command_prefix="~", intents=disnake.Intents.all(), case_insensitive=True)

# --- Auto play next sound ---
def play_next(ctx):
    global queue, current_title
    if queue and ctx.voice_client:
        filename, title = queue.pop(0)
        current_title = title

        def cleanup(error):
            try:
                os.remove(filename)
            except Exception as e:
                logging.error(f"Cleanup error: {e}")
            play_next(ctx)

        # запускаем трек
        ctx.voice_client.play(
            disnake.FFmpegOpusAudio(filename, executable="C:/Users/Panda/Desktop/New/bin/ffmpeg.exe"),
            after=cleanup
        )

        # отправляем сообщение о текущем треке сразу после запуска
        coro = ctx.send(f"Now playing:\n{current_title}")
        disnake.utils.asyncio.run_coroutine_threadsafe(coro, ctx.bot.loop)

        return title
    return None


# --- Bot commands ---
@bot.command()
async def play(ctx, url: str = None):
    global queue_counter
    try:
        if not url:
            await ctx.send("Please send a URL, e.g. `~play <url>`")
            return

        parsed = urlparse(url)
        domain = parsed.netloc

        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if not ctx.voice_client:
                await channel.connect()
        else:
            await ctx.send("Join a voice channel first!")
            return

        base_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "noplaylist": True,
            "quiet": True,
        }

        if "youtu.be" in url or "youtube.com" in url:
            await ctx.send("Youtube dont work, coming soon")

        elif "soundcloud.com" in url:
            sc_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio",
                "noplaylist": True,
                "quiet": True,
                "outtmpl": f"music/queue_{queue_counter}.%(ext)s",
            }

            with yt_dlp.YoutubeDL(sc_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            queue.append((filename, info.get("title")))
            queue_counter += 1

            if not ctx.voice_client.is_playing():
                title = play_next(ctx)
            else:
                await ctx.send(f"Added to queue: {info.get('title')}")

        elif "spotify.com" in url:
            await ctx.send("Spotify is not supported, sorry")

        else:
            await ctx.send(f"{domain} is not supported")

    except Exception as e:
        logging.error(f"Error 'play' command: {e}")
        await ctx.send("Error while using `~play`. Check logs.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped")
        play_next(ctx)
    elif ctx.voice_client:
        await ctx.send("Nothing is playing right now")
    else:
        await ctx.send("Bot is not connected to a voice channel")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Stopped")
        await ctx.voice_client.disconnect()

# --- Bot run ---
@bot.event
async def on_ready():
    print(f"Running {bot.user}")

bot.run(TOKEN)
