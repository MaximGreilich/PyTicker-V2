import discord
from discord.ext import commands, tasks
from datetime import datetime
import random


class Todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.todos = []
        self.check_deadlines.start()

    # --- GIF LISTEN ---

        # 1. PANIK (Wenn Deadline erreicht ist oder Prio 5 Stress)
        self.panic_gifs = [
          #  "https://media.giphy.com/media/hbOMqRWUkbeXDnjRYj/giphy.gif",  # Spongebob Feuer
            "https://media.giphy.com/media/1FMaabePDEfgk/giphy.gif",       # Big Bang Panik
            "https://media.giphy.com/media/HUkOv6BNWc1HO/giphy.gif",       # Spongebob rennen
            "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"        # Katze tippt schnell
        ]

        # 2. ERLEDIGT (Für den !done Befehl)
        self.party_gifs = [
            "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",  # The Office Party
            "https://media.giphy.com/media/kyLYXonQYYfwYDIeZl/giphy.gif",  # Elmo Party
           # "https://media.giphy.com/media/nVVVMDSXWmkBX0PC86/giphy.gif",  # Baby Yoda
            "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif"  # Homer Simpsin Relax
        ]

        # 3. WARNUNG (Bald fällig)
        self.nervous_gifs = [
            "https://media.giphy.com/media/LRVnPYqM8DLag/giphy.gif",       # Schwitzen
           # "https://media.giphy.com/media/3o7TKr3nzbh5RfBbQQ/giphy.gif",  # Uhr tickt
            "https://media.giphy.com/media/13Cmju3maIjStW/giphy.gif"       # Nervöser Spongebob
        ]

    def cog_unload(self):
        self.check_deadlines.cancel()

    # --- COMMAND: Add ---

    @commands.command()
    async def add(self, ctx, task_name: str, date_str: str, time_str: str, priority: int = 3):
        """Format: !add "Name" YYYY-MM-DD HH:MM 1-5"""
        if priority < 1 or priority > 5:
            await ctx.send("❌ Wichtigkeit muss zwischen 1 und 5 liegen.")
            return

        try:
            deadline_str = f"{date_str} {time_str}"
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")

            # Hinweis, falls man aus Versehen eine Vergangenheit wählt
            if deadline_dt < datetime.now():
                await ctx.send("⚠️ Info: Diese Deadline liegt in der Vergangenheit.")

            task_entry = {
                "task": task_name,
                "deadline": deadline_dt,
                "priority": priority,
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                "reminders_sent": []
            }

            self.todos.append(task_entry)
            prio_emoji = "🔥" * priority
            await ctx.send(f"✅ Aufgabe **'{task_name}'** gespeichert! (Prio {priority} {prio_emoji})")

        except ValueError:
            await ctx.send("❌ Formatfehler! Nutze: `!add \"Name\" YYYY-MM-DD HH:MM 1-5`")

    # --- COMMAND: Done ---
    @commands.command()
    async def done(self, ctx, index: int):
        """Löscht eine Aufgabe anhand ihrer Nummer in der Liste."""
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]

        # Gleiche Sortierung wie bei 'list', damit die Nummer stimmt
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        if index < 1 or index > len(user_tasks):
            await ctx.send("❌ Ungültige Nummer. Schau erst mit `!list` nach.")
            return

        # Aufgabe finden und aus der großen Liste löschen
        task_to_remove = user_tasks[index - 1]
        self.todos.remove(task_to_remove)

        await ctx.send(f"🗑️ Aufgabe **'{task_to_remove['task']}'** wurde erledigt/gelöscht.")

        # Zufälliges Party-GIF senden
        gif_url = random.choice(self.party_gifs)
        await ctx.send(gif_url)

    # --- COMMAND: List (mit Überfällig-Anzeige) ---
    @commands.command()
    async def list(self, ctx):
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]

        if not user_tasks:
            await ctx.send("Alles erledigt! 🏝️")
            return

        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        embed = discord.Embed(title="Deine To-Do Liste",
                              color=discord.Color.blue())

        for i, task in enumerate(user_tasks, 1):
            now = datetime.now()
            time_left = task["deadline"] - now
            fmt_time = task["deadline"].strftime("%d.%m. %H:%M")
            prio_str = "🔥" * task["priority"]

            # Logik für Text-Anzeige
            if time_left.total_seconds() < 0:
                # Vergangenheit
                past_minutes = int(abs(time_left.total_seconds()) / 60)
                if past_minutes > 60:
                    past_hours = past_minutes // 60
                    time_msg = f"🔴 **ÜBERFÄLLIG seit {past_hours} Stunden!**"
                else:
                    time_msg = f"🔴 **ÜBERFÄLLIG seit {past_minutes} Minuten!**"
            else:
                # Zukunft
                hours_left = int(time_left.total_seconds() / 3600)
                time_msg = f"Zeit übrig: {hours_left}h ({fmt_time})"

            value_text = f"{time_msg}\n**Prio:** {prio_str}"
            embed.add_field(
                name=f"{i}. {task['task']}", value=value_text, inline=False)

        await ctx.send(embed=embed)

    # --- HINTERGRUND LOGIK ---
    @tasks.loop(seconds=10)
    async def check_deadlines(self):
        now = datetime.now()

        for task in self.todos:
            time_left = task["deadline"] - now
            minutes_left = time_left.total_seconds() / 60
            priority = task["priority"]

            # Benachrichtigungen definieren
            if priority == 5:
                milestones = [1440, 720, 360, 180, 60, 30, 15, 10, 5, 0]
            elif priority == 4:
                milestones = [1440, 360, 60, 30, 10, 0]
            elif priority == 3:
                milestones = [1440, 180, 60, 10, 0]
            elif priority == 2:
                milestones = [1440, 60, 0]
            else:
                milestones = [1440, 0]

            for milestone in milestones:
                # Prüfbereich: Ist die Zeit gerade am Meilenstein vorbei?
                # Wir prüfen: Zeit ist kleiner als Meilenstein, aber nicht länger als 2 Min her
                if minutes_left <= milestone and minutes_left > milestone - 2:

                    if milestone not in task["reminders_sent"]:
                        channel = self.bot.get_channel(task["channel_id"])
                        if channel:
                            if milestone == 0:
                                await channel.send(f"🚨 **DEADLINE ERREICHT!** <@{task['user_id']}>\nDie Aufgabe **'{task['task']}'** ist fällig! (Bitte mit `!done` abhaken)")

                                await channel.send(random.choice(self.panic_gifs))
                            elif milestone <= 10 and priority >= 4:
                                await channel.send(f"⚠️ **SOFORT!** <@{task['user_id']}>\nNur noch {milestone} Minuten für **'{task['task']}'**!")
                                await channel.send(random.choice(self.nervous_gifs))
                            elif milestone <= 60:
                                await channel.send(f"⏳ **Bald fällig!** <@{task['user_id']}>\nNoch {milestone} Minuten für **'{task['task']}'**.")
                            else:
                                hours = milestone // 60
                                await channel.send(f"⏰ **Erinnerung:** Noch {hours} Stunden bis **'{task['task']}'**.")

                        task["reminders_sent"].append(milestone)

    @check_deadlines.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Todo(bot))
