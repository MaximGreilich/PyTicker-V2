import discord
import asyncio
import os
from discord.ext import commands

TOKEN = 'DEIN_TOKEN'

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} ist bereit!')

async def load_extensions():
    # Lädt alle Dateien im Ordner 'cogs', die auf .py enden
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            # cogs.todo laden (das .py weglassen)
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Cog geladen: {filename}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())