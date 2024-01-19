import fastapi
import discord
import asyncio
import requests
from fastapi import HTTPException
from pydantic import BaseModel
from discord.ext import commands
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import socket
from httpx import AsyncClient
import openai
import aiohttp
from functools import partial
import os
from decouple import config

app = fastapi.FastAPI()
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True


BOT_TOKEN = config('BOT_TOKEN')
SHARD_ID = int(config('SHARD_ID', default=0))
SHARD_COUNT = int(config('SHARD_COUNT', default=1))
OPENAI_API_KEY = config('OPENAI_API_KEY')
CHANNEL_ID = 1170336672722976821
openai.api_key = OPENAI_API_KEY
bot_emote_channel_id = 1191693037315829851

bot = commands.AutoShardedBot(command_prefix="!", intents=discord.Intents.all(),shard_count=SHARD_COUNT, shard_id=SHARD_ID)



class MessageRequest(BaseModel):
    message: str

async_executor = ThreadPoolExecutor()
    

@app.get("/")
async def hello_world():
    return {"hello": "world"}

@app.get("/api/info")
async def get_bot_info():
    return {"bot_name": bot.user.name, "bot_id": bot.user.id}

@bot.command()
async def welcome(ctx:commands.Context, member:discord.Member):
    await ctx.send(f"Welcome to {ctx.guild.name}, {member.mention}!")

@bot.command(name='reactrole', help='React to a message to get or remove the role.')
async def react_role(ctx):
    
    emote = "👍"
    message_content = f"React with {emote} to get or remove the '{"Members"}' role!"
    message = await ctx.send(message_content)
    await message.add_reaction(emote)

    print(f"React to the message with '{emote}' to get or remove the role.")

@bot.event
async def on_reaction_add(reaction, user):
    await toggle_role(reaction, user)

@bot.event
async def on_reaction_remove(reaction, user):
    await toggle_role(reaction, user)

async def toggle_role(reaction, user):
    if reaction.message.id == bot_emote_channel_id and str(reaction.emoji) == "👍":
        role = discord.utils.get(user.guild.roles, name="Members")

        if role:
            if reaction.emoji in [r.emoji for r in reaction.message.reactions]:
                if reaction.emoji == "👍":
                    await user.add_roles(role)
                    print(f"{user.name} has been given the role: {role.name}")
                else:
                    await user.remove_roles(role)
                    print(f"{user.name} has removed the role: {role.name}")


async_executor = ThreadPoolExecutor()

@bot.command(name='ask_gpt', help='Ask GPT-3 a question.')
async def ask_gpt(ctx, *, question):
    try:
        previous_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question},
        ]

       
        loop = asyncio.get_event_loop()

      
        partial_func = partial(openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=previous_messages,
        )

        response = await loop.run_in_executor(async_executor, partial_func)

        generated_text = response['choices'][0]['message']['content'].strip()

        await ctx.send(f'GPT-3 says: {generated_text}')

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")



@bot.command(name="sendmessage", help='Send messages in a specific channel.')
async def send_message_to_channel(ctx, channel: discord.TextChannel, *, message: str):
    try:
        
        await channel.send(f"@everyone {message}")
        return {"status": "Message sent"}
    except Exception as e:
       
        return {"status": f"Error: {str(e)}"}
    

async def process_task(number):
    
    await asyncio.sleep(5)
    return {"result": number ** 2}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.command(name='get_crypto_price', help='Get cryptocurrency price. ')
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

@bot.command(name='poll', help='Create a poll with a question.')
async def poll(ctx, *, question):
  
    poll_embed = discord.Embed(
        title='📊 Poll',
        description=question,
        color=0x3498db  
    )
    poll_embed.set_footer(text=f'Poll started by {ctx.author.display_name}')

   
    poll_message = await ctx.send(embed=poll_embed)
    await poll_message.add_reaction('👍')  
    await poll_message.add_reaction('👎')  

   
    await ctx.message.delete()


@bot.command(name="changerole", help='Change a role for a member.')
async def change_role(ctx, member: discord.Member, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if role is None:
        await ctx.send(f"Role {role_name} not found.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"{member.mention} has been given the {role_name} role.")
    except discord.Forbidden:
        await ctx.send("I don't have the necessary permissions to change roles.")

@bot.command(name="removerole", help='Remove a role for a member')
async def remove_role(ctx, member: discord.Member, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if role is None:
        await ctx.send(f"Role {role_name} not found.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been removed from the {role_name} role.")
    except discord.Forbidden:
        await ctx.send("I don't have the necessary permissions to change roles.")


async def run():
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        await bot.logout()

asyncio.create_task(run())

