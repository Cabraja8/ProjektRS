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
openai.api_key = OPENAI_API_KEY
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
    try:
        ROLE_EMOTE_CHANNEL_ID = 1191693037315829851
        role_name = 'Members'

        if ctx.channel.id == ROLE_EMOTE_CHANNEL_ID:
            emote = "👍"
            message_content = f"React with {emote} to get or remove the '{role_name}' role!"
            async with ctx.typing(): 
                message = await ctx.send(message_content)
            await message.add_reaction(emote)

            await ctx.send(f"React to the message with '{emote}' to get or remove the '{role_name}' role.")

            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role:
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) == emote

                async with ctx.typing():  
                    reaction, user = await bot.wait_for('reaction_add', check=check)
                member: discord.Member = user

                if reaction.emoji == emote:
                    await member.add_roles(role)
                    await ctx.send(f"Role '{role_name}' has been added to {member.display_name}.")
                else:
                    await member.remove_roles(role)
                    await ctx.send(f"Role '{role_name}' has been removed from {member.display_name}.")
            else:
                await ctx.send(f"Role '{role_name}' not found.")
        else:
            await ctx.send('⚠️ This command can only be used in the designated role-emote channel.')
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.event
async def on_shard_ready(shard_id):
    print(f'Shard #{shard_id} is ready')

@bot.command(name='ask_gpt', help='Ask GPT-3 a question.')
async def ask_gpt(ctx, *, question):
    GPT_3_CHANNEL_ID = 1191367082613428254

    if ctx.channel.id == GPT_3_CHANNEL_ID:
        try:
           
            async with ctx.typing():
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
    else:
        await ctx.send('⚠️ This command can only be used in the designated GPT-3 channel.')

@bot.command(name="sendmessage", help='Send messages in a specific channel.')
async def send_message_to_channel(ctx, channel: discord.TextChannel, *, message: str):
    SEND_MESSAGE_CHANNEL_ID = 1202637167659188266

    if ctx.channel.id == SEND_MESSAGE_CHANNEL_ID:
        try:
            async with ctx.typing(): 
                await channel.send(f"{message}")
            await ctx.send("Message sent successfully.")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
    else:
        await ctx.send("⚠️ This command is intended to be used in the designated send message channel.")

@bot.command(name="sendmessageall", help='Send messages in a specific channel.')
async def send_message_to_channel(ctx, channel: discord.TextChannel, *, message: str):
    SEND_MESSAGE_CHANNEL_ID = 1202637167659188266

    if ctx.channel.id == SEND_MESSAGE_CHANNEL_ID:
        try:
             async with ctx.typing(): 
                 await channel.send(f"@everyone {message}")
                 await ctx.send("Message sent successfully.")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
    else:
        await ctx.send("⚠️ This command is intended to be used in the designated send message channel.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.command(name='get_crypto_price', help='Get cryptocurrency price.')
async def get_crypto_price(ctx, vs_currency='eur'):
    CRYPTO_PRICE_CHANNEL_ID = 1183035389334798338

    if ctx.channel.id == CRYPTO_PRICE_CHANNEL_ID:
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

        async with ctx.typing():  
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
    POLL_CHANNEL_ID = 1202637430277144646
    
    if ctx.channel.id == POLL_CHANNEL_ID:
        async with ctx.typing():  
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
    else:
        await ctx.send("⚠️ This command is intended to be used in the designated poll channel.")

@bot.command(name="changerole", help='Change a role for a member.')
async def change_role(ctx, member: discord.Member, role_name: str):
    ROLE_CHANGER_CHANNEL_ID = 1202637204296306749
    
    if ctx.channel.id == ROLE_CHANGER_CHANNEL_ID:
        async with ctx.typing():  
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if role is None:
                await ctx.send(f"Role {role_name} not found.")
                return

            try:
                await member.add_roles(role)
                await ctx.send(f"{member.mention} has been given the {role_name} role.")
            except discord.Forbidden:
                await ctx.send("I don't have the necessary permissions to change roles.")
    else:
        await ctx.send("⚠️ This command is intended to be used in the designated role changer channel.")

@bot.command(name="removerole", help='Remove a role for a member')
async def remove_role(ctx, member: discord.Member, role_name: str):
    ROLE_CHANGER_CHANNEL_ID = 1202637204296306749
    
    if ctx.channel.id == ROLE_CHANGER_CHANNEL_ID:
        async with ctx.typing():  
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            if role is None:
                await ctx.send(f"Role {role_name} not found.")
                return

            try:
                await member.remove_roles(role)
                await ctx.send(f"{member.mention} has been removed from the {role_name} role.")
            except discord.Forbidden:
                await ctx.send("I don't have the necessary permissions to change roles.")
    else:
        await ctx.send("⚠️ This command is intended to be used in the designated role changer channel.")


async def run():
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        await bot.logout()

asyncio.create_task(run())

