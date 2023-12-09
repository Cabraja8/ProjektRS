import fastapi
import discord
import asyncio
import requests
from fastapi import HTTPException
from pydantic import BaseModel
from discord.ext import commands

app = fastapi.FastAPI()


BOT_TOKEN = 'MTE2OTY4MTE5MjczMjMzNjMxMA.GIjaHb.FfYzPW4irOYRUXO5XD__zEuTWqjnXuEBu6ixOk'

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
    CHANNEL_ID = 1170336672722976821
    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    await channel.send(message)
    return {"status": "Message sent"}

@bot.command()
async def welcome(ctx:commands.Context, member:discord.Member):
    await ctx.send(f"Welcome to {ctx.guild.name}, {member.mention}!")
    


@bot.command(name='get_crypto_price', help='Get cryptocurrency price')
async def get_crypto_price(ctx, vs_currency='usd'):
    CHANNEL_ID = 1183035389334798338

    if ctx.channel.id == CHANNEL_ID:
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': vs_currency,
            'order': 'market_cap_desc',
            'per_page': 5,  
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '1h,24h,7d',  
            'ids': 'bitcoin,ethereum,binancecoin,ripple,litecoin',  
        }

        response = requests.get(url, params=params)
        data = response.json()

        for crypto in data:
            name = crypto.get('name')
            symbol = crypto.get('symbol')
            price = crypto.get('current_price')

            message = f'{name} ({symbol}): {vs_currency} {price}\n'
            await ctx.send(message)
    else:
        await ctx.send('This command can only be used in crypto-price-show channel.')



async def run():
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        await bot.logout()

asyncio.create_task(run())