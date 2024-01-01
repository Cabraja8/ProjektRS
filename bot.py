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
from config import API_KEY,TOKEN

app = fastapi.FastAPI()
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

BOT_TOKEN = 'MTE2OTY4MTE5MjczMjMzNjMxMA.GTvPum.d4yI2_xNI9tVdIBG37S3yXwS8xikiJED2bgKyk'
openai.api_key = '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'
CHANNEL_ID = 1170336672722976821

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())



class MessageRequest(BaseModel):
    message: str




@app.get("/")
async def hello_world():
    return {"hello": "world"}

@app.get("/api/info")
async def get_bot_info():
    return {"bot_name": bot.user.name, "bot_id": bot.user.id}

@bot.command()
async def welcome(ctx:commands.Context, member:discord.Member):
    await ctx.send(f"Welcome to {ctx.guild.name}, {member.mention}!")

@bot.command(name='gpt', help='Generate text using GPT-3')
async def generate_text(ctx, *, prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        generated_text = response.choices[0].text.strip()
        await ctx.send(f'Generated Text: {generated_text}')
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command(name="commands", help="Show all available commands with descriptions")
async def show_commands(ctx):
    command_list = []
    
    
    for command in bot.commands:
        if command.hidden:
            continue  
        command_list.append(f"**{command.name}**: {command.help}")

 
    commands_message = "\n".join(command_list)

  
    await ctx.send(f"**Available Commands**\n\n{commands_message}")


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

