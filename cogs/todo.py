import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import json
import os


class Todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.todos = []
        self.filename = "saved_tasks.json"  # Dateiname für gespeicherte Aufgaben

        # Lade gespeicherte Aufgaben beim Start
        self.load_tasks()
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

    # --- SPEICHERN & LADEN ---
    def save_tasks(self):
        data_to_save = []
        for task in self.todos:
            entry = task.copy()
            # In ISO-Format konvertieren
            entry["deadline"] = task["deadline"].isoformat()
            data_to_save.append(entry)

        with open(self.filename, 'w') as f:
            json.dump(data_to_save, f, indent=4)

    def load_tasks(self):
        if not os.path.exists(self.filename):
            return  # Datei existiert nicht, nichts zu laden

        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)

            self.todos = []
            for entry in data:
                entry["deadline"] = datetime.fromisoformat(entry["deadline"])
                self.todos.append(entry)
            print(f"📂 {len(self.todos)} Aufgaben geladen.")
        except Exception as e:
            print(f"❌ Fehler beim Laden: {e}")

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
            self.save_tasks()  # Aufgaben speichern

            prio_emoji = "🔥" * priority
            await ctx.send(f"✅ Aufgabe **'{task_name}'** gespeichert! (Prio {priority} {prio_emoji})")

        except ValueError:
            await ctx.send("❌ Formatfehler! Nutze: `!add \"Name\" YYYY-MM-DD HH:MM 1-5`")

    # --- COMMAND: Done ---
    @commands.command()
    async def done(self, ctx, index: int):
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        # Gleiche Sortierung wie bei 'list', damit die Nummer stimmt
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        if index < 1 or index > len(user_tasks):
            await ctx.send("❌ Ungültige Nummer. Schau erst mit `!list` nach.")
            return

        # Aufgabe finden und aus der großen Liste löschen
        task_to_remove = user_tasks[index - 1]
        self.todos.remove(task_to_remove)
        self.save_tasks()  # Aufgaben speichern

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
# --- COMMAND: Motivation ---

    @commands.command(aliases=["moti"])  # Reagiert auf !motivation und !moti
    async def motivation(self, ctx):

        # Eine Liste mit Sprüchen (kannst du beliebig erweitern)
        quotes = [
            "🌟 Der beste Weg, die Zukunft vorherzusagen, ist, sie zu erschaffen.",
            "“Sometimes life is like a dark tunnel. You can’t always see the light at the end of the tunnel, but if you just keep moving…you will come to a better place.” ,     -Uncle Iroh",
            "“Ihr müsst es umsetzen…durch Theorien ist noch nie jemand ans Ziel gekommen” - Arda Saatçi",
            "“This shit takes time” -Will Tenny",
            "Storms make trees take deeper roots.",
            "If you quit now, you'll end up right back where you first began. And when you first began, you were desperate to be where you are right now.",
            "One day or Day One. You decide.",
            "Rome wasn't built in a day.",
            "Hard work beats talent when talent doesn't work hard."


        ]

        # Zufälligen Spruch auswählen
        spruch = random.choice(quotes)

        await ctx.send(f"💪 **Motivation für dich:**\n\n_{spruch}_")
        
    # --- COMMAND: Snooze (Aufschieben) ---
    @commands.command(aliases=["snooze", "later", "verschieben"])
    async def delay(self, ctx, index: int, minutes: int):
        
        # 1. Liste holen und sortieren (damit der Index stimmt)
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        if index < 1 or index > len(user_tasks):
            await ctx.send("❌ Diese Nummer gibt es nicht.")
            return

        # 2. Aufgabe bearbeiten
        task = user_tasks[index - 1]
        
        # Alte Zeit merken
        old_time = task["deadline"]
        
        # Neue Zeit berechnen (Alte Zeit + Minuten)
        new_time = old_time + timedelta(minutes=minutes)
        task["deadline"] = new_time
        
        # WICHTIG: Die Liste "reminders_sent" leeren, damit er nochmal warnt!
        task["reminders_sent"] = []
        
        # 3. Speichern
        self.save_tasks()
        
        # 4. Feedback geben
        fmt_old = old_time.strftime("%H:%M")
        fmt_new = new_time.strftime("%H:%M")
        
        await ctx.send(f"💤 Aufgabe **'{task['task']}'** verschoben.\nVon {fmt_old} Uhr ➡️ auf **{fmt_new} Uhr** (+{minutes} min).")

    # --- COMMAND: Zeit prüfen ---
    @commands.command(aliases=["check", "zeit"])
    async def time(self, ctx, index: int):

        # 1. Aufgaben holen und genau so sortieren wie bei !list
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]

        # WICHTIG: Die Sortierung muss exakt gleich sein wie in 'list',
        # damit "Aufgabe 1" hier auch wirklich "Aufgabe 1" ist.
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        if index < 1 or index > len(user_tasks):
            await ctx.send("❌ Diese Nummer gibt es nicht. Schau mit `!list` nach.")
            return

        # 2. Aufgabe auswählen
        task = user_tasks[index - 1]
        now = datetime.now()
        diff = task["deadline"] - now

        # 3. Zeit berechnen
        total_seconds = int(diff.total_seconds())

        if total_seconds < 0:
            # Wenn die Zeit abgelaufen ist
            past_s = abs(total_seconds)
            days = past_s // 86400
            hours = (past_s % 86400) // 3600
            minutes = (past_s % 3600) // 60

            msg = f"🔴 Die Deadline für **'{task['task']}'** ist vorüber!\n"
            msg += f"Seit: **{days} Tagen, {hours} Stunden und {minutes} Minuten**."
            await ctx.send(msg)

        else:
            # Wenn noch Zeit ist
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            prio_emoji = "🔥" * task["priority"]

            embed = discord.Embed(
                title=f"⏳ Zeit-Check: {task['task']}", color=discord.Color.green())
            embed.add_field(name="Verbleibende Zeit",
                            value=f"**{days}** Tage, **{hours}** Stunden, **{minutes}** Minuten", inline=False)
            embed.add_field(name="Deadline", value=task["deadline"].strftime(
                "%d.%m.%Y um %H:%M Uhr"), inline=True)
            embed.add_field(
                name="Wichtigkeit", value=f"{task['priority']} {prio_emoji}", inline=True)

            await ctx.send(embed=embed)
            
        # --- COMMAND: Hilfe / Anleitung ---
    @commands.command(aliases=["hilfe", "guide", "commands"])
    async def manual(self, ctx):
        """Zeigt eine schöne Übersicht aller Befehle."""
        
        embed = discord.Embed(title="🤖 Dein Bot-Handbuch", description="Hier sind alle Befehle, die ich verstehe:", color=discord.Color.gold())
        
        # 1. Die Wichtigsten
        embed.add_field(
            name="📝 Aufgaben verwalten", 
            value=(
                "`!add \"Name\" YYYY-MM-DD HH:MM [1-5]`\n"
                "Erstellt eine Aufgabe. Wichtigkeit (1-5) ist optional.\n"
                "*Bsp: !add \"Mathe\" 2025-05-20 14:00 5*\n\n"
                "`!list`\n"
                "Zeigt alle deine offenen Aufgaben sortiert nach Wichtigkeit.\n\n"
                "`!done <Nummer>`\n"
                "Markiert die Aufgabe als erledigt und löscht sie.\n"
                "*Bsp: !done 1*"
            ),
            inline=False
        )

        # 2. Zeit & Planung
        embed.add_field(
            name="⏰ Zeit & Planung",
            value=(
                "`!time <Nummer>` (oder `!check`)\n"
                "Zeigt exakt an, wie viel Zeit für Aufgabe X noch bleibt.\n\n"
                "`!delay <Nummer> <Minuten>` (oder `!snooze`)\n"
                "Verschiebt die Deadline um X Minuten nach hinten.\n"
                "*Bsp: !snooze 1 30* (30 Min später)"
            ),
            inline=False
        )

        # 3. Extras
        embed.add_field(
            name="✨ Sonstiges",
            value=(
                "`!moti` (oder `!motivation`)\n"
                "Gibt dir einen zufälligen Motivationsspruch.\n\n"
                "`!hilfe`\n"
                "Zeigt diese Nachricht an."
            ),
            inline=False
        )
        
        embed.set_footer(text="Tipp: Aufgaben werden automatisch gespeichert! 💾")
        
        await ctx.send(embed=embed)

    # --- COMMAND: Snooze (Aufschieben) ---
    @commands.command(aliases=["snooze", "later", "verschieben"])
    async def delay(self, ctx, index: int, minutes: int):
        """Verschiebt die Deadline einer Aufgabe um X Minuten."""

        # 1. Liste holen und sortieren (damit der Index stimmt)
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        if index < 1 or index > len(user_tasks):
            await ctx.send("❌ Diese Nummer gibt es nicht.")
            return

        # 2. Aufgabe bearbeiten
        task = user_tasks[index - 1]

        # Alte Zeit merken
        old_time = task["deadline"]

        # Neue Zeit berechnen (Alte Zeit + Minuten)
        new_time = old_time + timedelta(minutes=minutes)
        task["deadline"] = new_time

        # WICHTIG: Die Liste "reminders_sent" leeren, damit er nochmal warnt!
        task["reminders_sent"] = []

        # 3. Speichern
        self.save_tasks()

        # 4. Feedback geben
        fmt_old = old_time.strftime("%H:%M")
        fmt_new = new_time.strftime("%H:%M")

        await ctx.send(f"💤 Aufgabe **'{task['task']}'** verschoben.\nVon {fmt_old} Uhr ➡️ auf **{fmt_new} Uhr** (+{minutes} min).")

    # --- HINTERGRUND LOGIK ---
    @tasks.loop(seconds=10)
    async def check_deadlines(self):
        now = datetime.now()
        data_changer = False  # Flag, um zu prüfen, ob wir speichern müssen

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
                        data_changed = True

        if data_changed:
            self.save_tasks()  # Änderungen speichern

    @check_deadlines.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Todo(bot))
