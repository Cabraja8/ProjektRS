import fastapi
import discord
import asyncio
import requests
from fastapi import HTTPException
from pydantic import BaseModel
from discord.ext import commands

app = fastapi.FastAPI()


BOT_TOKEN = 'MTE2OTY4MTE5MjczMjMzNjMxMA.G5LLIE.wog9y3Sm3QMRm6nDb1U119EFT9aeqdJa95bLPQ'

CHANNEL_ID = 1170336672722976821

bot = commands.Bot(command_prefix="!",intents=discord.Intents.all())

class MessageRequest(BaseModel):
    message: str

@app.get("/")
async def hello_world():
    return {"hello": "world"}

@app.get("/api/info")
async def get_bot_info():
    return {"bot_name": bot.user.name, "bot_id": bot.user.id}

@app.post("/api/send-message/{message}")
async def send_discord_message(message: str):
    # Replace this with your Discord channel ID
    CHANNEL_ID = 1170336672722976821
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    await channel.send(message)
    return {"status": "Message sent"}

@bot.command()
async def welcome(ctx:commands.Context, member:discord.Member):
    await ctx.send(f"Welcome to {ctx.guild.name}, {member.mention}!")
    
@app.get("/api/guilds")
async def list_guilds():
    guilds = [guild.name for guild in bot.guilds]
    return {"guilds": guilds}

# Run your Discord bot and FastAPI app together

async def run():
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        await bot.logout()

asyncio.create_task(run())