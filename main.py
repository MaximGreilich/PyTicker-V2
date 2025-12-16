import discord
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv  # Neu importieren

# 1. Lade die Variablen aus der .env Datei
load_dotenv()

# 2. Hol den Token sicher ab
TOKEN = os.getenv('DISCORD_TOKEN')

# Sicherheitscheck: Falls kein Token gefunden wurde
if TOKEN is None:
    print("FEHLER: Kein Token in der .env Datei gefunden!")
    exit()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'✅ Eingeloggt als {bot.user} (ID: {bot.user.id})')
    print('------')


async def load_extensions():
    # Prüfen, ob der Ordner 'cogs' existiert
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'⚙️  Cog geladen: {filename}')
                except Exception as e:
                    print(f'❌ Fehler beim Laden von {filename}: {e}')
    else:
        print("⚠️  Ordner 'cogs' nicht gefunden.")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Verhindert hässliche Fehlermeldungen beim Beenden mit STRG+C
        pass
