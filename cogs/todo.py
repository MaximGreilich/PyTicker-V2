import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import json
import os
import re

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

    @commands.command(aliases=["add"])
    async def neu(self, ctx, task_name: str = None, date_str: str = None, time_str: str = None, priority: int = 3, neue_id: int = None):
        if priority < 1 or priority > 5:
            await ctx.send("❌ Wichtigkeit muss zwischen 1 und 5 liegen.")
            return
        
        if task_name is None or date_str is None or time_str is None:
            await ctx.send("❌ Fehlende Argumente! Nutze: `!add \"Name\" DD.MM.YYYY HH:MM 1-5`")
            return

         # Datum und Zeit parsen

        try:
            deadline_str = f"{date_str} {time_str}"
            deadline_dt = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")

            # Hinweis, falls man aus Versehen eine Vergangenheit wählt
            if deadline_dt < datetime.now():
                await ctx.send("⚠️ Info: Diese Deadline liegt in der Vergangenheit.")
                
                        # Error handling für Aufgabennamen
        

            task_entry = {
                "task": task_name,
                "deadline": deadline_dt,
                "priority": priority,
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id,
                
            }
            

            self.todos.append(task_entry)
            self.save_tasks()  # Aufgaben speichern
            
            meine_aufgaben = self.get_tasks_for_user(ctx.author.id)
            meine_nummer = len(meine_aufgaben)
            

            prio_emoji = "🔥" * priority
            await ctx.send(f"✅ Aufgabe **'{task_name}'** gespeichert! (Prio {priority} {prio_emoji}) (ID: {neue_id})")

        except ValueError:
            await ctx.send("❌ Formatfehler! Nutze: `!add \"Name\" DD.MM.YYYY HH:MM 1-5`")

    # --- COMMAND: Done ---
    @commands.command(aliases=["done"])
    async def fertig(self, ctx, * , eingabe: str = None):
        if eingabe is None:
            await ctx.send("❌ Was hast du erledigt? Gib eine **Nummer** oder den **Namen** an.")
            return

        meine_aufgaben = self.get_tasks_for_user(ctx.author.id)
        meine_aufgaben.sort(key=lambda x: (-x["priority"], x["deadline"]))
        
        to_remove = None
        #Fall A: Nummer
        if eingabe.isdigit():
            nummer = int(eingabe)
            if 1 <= nummer <= len(meine_aufgaben):
                to_remove = meine_aufgaben[nummer - 1]
            else:
                await ctx.send("❌ Diese Nummer gibt es nicht.")
                return
        
        #Fall B: Name
        else:
            for task in meine_aufgaben:
                if task["task"].lower() == eingabe.lower():
                    to_remove = task
                    break
            if to_remove is None:
                await ctx.send("❌ Diese Aufgabe wurde nicht gefunden.")
                return
        if to_remove:
            if to_remove in self.todos:
                self.todos.remove(to_remove)
                self.save_tasks()
                await ctx.send(f"✅ Aufgabe **'{to_remove['task']}'** als erledigt markiert!")
            else:
                await ctx.send("❌ Aufgabe nicht in der Hauptliste gefunden.")
        else:
            await ctx.send("❌ Aufgabe nicht gefunden.")
            
        # Zufälliges Party-GIF senden
        gif_url = random.choice(self.party_gifs)
        await ctx.send(gif_url)

    # --- COMMAND: List (mit Überfällig-Anzeige) ---
    @commands.command(aliases=["list"])
    async def liste(self, ctx):
        #Aufgaben des Users filtern
        meine_aufgaben = [t for t in self.todos if t["user_id"] == ctx.author.id]
        
        if not meine_aufgaben:
            await ctx.send("✅ Du hast keine offenen Aufgaben! Gut gemacht! 🎉")
            return
        
        # Aufgaben sortieren (z.B. nach Deadline und Priorität)
        meine_aufgaben.sort(key=lambda x: (-x["priority"], x["deadline"]))
        embed = discord.Embed(title=f"📝 Aufgabenliste für {ctx.author.name}", color=discord.Color.blue())
        
        text = ""
        #enumerate für Nummerierung
        for index, task in enumerate(meine_aufgaben, start=1):
            zeit_str= task["deadline"].strftime("%d.%m.%Y %H:%M")
            prio = "🔥" * task["priority"]
            
            #String bauen
            text += f"**{index}.** {task['task']} (bis {zeit_str}) {prio}\n"
        embed.description = text
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
        

 # --- COMMAND: Smart Snooze (Umbenannt zum Testen) ---
    @commands.command(aliases=["snooze", "delay"])
    async def verschieben(self, ctx, index: int, *, time_input: str): 
        
        """""
        Verschiebt eine Deadline.
        Beispiele: !delay 1 2h (oder 2std), !delay 1 10m, !delay 1 1d (oder 1t)
        """
        
        # 1. Liste holen
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]
        user_tasks.sort(key=lambda x: (-x["priority"], x["deadline"]))

        if index < 1 or index > len(user_tasks):
            await ctx.send("❌ Diese Nummer gibt es nicht.")
            return

        # 2. Text säubern (Kleinbuchstaben, Leerzeichen weg)
        # Aus "2 STD" wird "2std"
        clean_input = time_input.lower().replace(" ", "")

        days = 0
        hours = 0
        minutes = 0

       #  Regulären Ausdruck nutzen, um Zahlen + Einheiten zu finden
        matches = re.findall(r"(\d+)([a-z]+)", clean_input)

        if not matches:
            # Fallback: Wenn nur eine Zahl da steht (z.B. "30")
            if clean_input.isdigit():
                minutes = int(clean_input)
            else:
                await ctx.send(f"❌ Konnte die Zeit '{time_input}' nicht verstehen.\nVersuche: `2h`, `30m`, `1d`.")
                return

        # Werte zusammenrechnen
        for amount, unit in matches:
            val = int(amount)
            
            if unit in ['d', 't', 'tag', 'tage']:
                days += val
            elif unit in ['h', 's', 'std', 'stunde']:
                hours += val
            elif unit in ['m', 'min', 'minute']:
                minutes += val
            else:
                await ctx.send(f"⚠️ Die Einheit '{unit}' kenne ich nicht (nutze d/h/m).")

        # Wenn alles 0 ist (z.B. bei falscher Einheit)
        if days == 0 and hours == 0 and minutes == 0:
             await ctx.send("❌ Keine gültige Zeit gefunden.")
             return

        # 3. Speichern & Ändern
        task = user_tasks[index - 1]
        old_time = task["deadline"]
        new_time = old_time + timedelta(days=days, hours=hours, minutes=minutes)
        
        task["deadline"] = new_time
        task["reminders_sent"] = [] 
        self.save_tasks()
        
        # 4. Feedback
        fmt_old = old_time.strftime("%d.%m. %H:%M")
        fmt_new = new_time.strftime("%d.%m. %H:%M")
        
        # Text bauen
        diff_text = []
        if days > 0: diff_text.append(f"{days}d")
        if hours > 0: diff_text.append(f"{hours}h")
        if minutes > 0: diff_text.append(f"{minutes}m")
        
        await ctx.send(f"💤 Aufgabe **'{task['task']}'** verschoben.\nVon {fmt_old} Uhr ➡️ auf **{fmt_new} Uhr** (+{' '.join(diff_text)}).")

    # --- COMMAND: Zeit prüfen ---
    @commands.command(aliases=["check", "time"])
    async def zeit(self, ctx, index: int):

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
    @commands.command(aliases=["guide", "commands"])
    async def hilfe(self, ctx):
        """Zeigt die Befehlsübersicht an."""
        
        beschreibung = (
            "**📝 Neue Aufgabe erstellen**\n"
            "Nutze `!neu`, Titel in Anführungszeichen, Datum und optional die Wichtigkeit (1-5).\n"
            "> Bsp: `!neu \"Mathe\" 20.05.2025 14:00 5` (5 = sehr wichtig)\n\n"
            
            "**📋 Liste anzeigen**\n"
            "Mit `!liste` (oder `!list`) siehst du alle offenen Aufgaben und wie viel Zeit noch bleibt.\n\n"
            
            "**✅ Aufgabe erledigen**\n"
            "Nutze `!fertig` (oder `!done`) und die Nummer der Aufgabe aus der Liste.\n"
            "> Bsp: `!fertig 1`\n\n"
            
            "**🗑️ Aufgabe loeschen**\n"
            "Wenn du dich vertippt hast: `!loeschen` (oder `!del`) entfernt sie, ohne Punkte/Erfolg.\n"
            "> Bsp: `!loeschen 2`\n\n"
            
            "**⏰ Zeit verschieben**\n"
            "Brauchst du mehr Zeit? Nutze `!verschieben` (oder `!delay`).\n"
            "> Bsp: `!verschieben 1 30m` (30 Min später)\n"
            "> Bsp: `!verschieben 1 1d` (1 Tag später)\n\n"
            
            "**💪 Motivation**\n"
            "Tippe `!motivation` für einen zufälligen Spruch.\n\n"

            "**❓ Hilfe**\n"
            "Zeigt diese Übersicht erneut an: `!hilfe`"
        )

        embed = discord.Embed(
            title="📚 Bot-Handbuch",
            description=beschreibung,
            color=discord.Color.gold()
        )
        
        embed.set_footer(text="Tipp: Datum ist immer Tag.Monat.Jahr")

        await ctx.send(embed=embed)
        

    # --- COMMAND: Delete (Löschen) ---
    @commands.command(aliases=["del", "remove"])
    async def loeschen(self, ctx, nummer: int):
        """Löscht eine Aufgabe anhand ihrer Nummer in DEINER Liste."""
        
        # 1. Wir holen nur DEINE Aufgaben
        meine_aufgaben = self.get_user_tasks(ctx.author.id)
        
        # 2. Wenn du gar keine Aufgaben hast, können wir nichts löschen
        if not meine_aufgaben:
            await ctx.send("❌ Du hast gar keine Aufgaben, die du löschen könntest.")
            return

        # 3. WICHTIG: Sortieren! (Muss exakt gleich sein wie bei !liste)
        # Wir sortieren nach Deadline, damit "Nummer 1" auch wirklich die erste Aufgabe ist
        meine_aufgaben.sort(key=lambda t: t["deadline"])

        # 4. Prüfen, ob die Nummer gültig ist
        # (User tippt 1, Python zählt ab 0 -> daher "nummer - 1")
        if 1 <= nummer <= len(meine_aufgaben):
            
            # Das ist das Objekt, das der User meint:
            zu_loeschende_aufgabe = meine_aufgaben[nummer - 1]
            
            # 5. Jetzt löschen wir dieses Objekt aus der GLOBALEN Liste (self.todos)
            if zu_loeschende_aufgabe in self.todos:
                self.todos.remove(zu_loeschende_aufgabe)
                self.save_tasks() # Speichern nicht vergessen!
                
                await ctx.send(f"🗑️ Aufgabe **'{zu_loeschende_aufgabe['task']}'** wurde gelöscht.")
            else:
                # Das sollte eigentlich nie passieren, außer die DB ist korrupt
                await ctx.send("❌ Fehler: Konnte die Aufgabe in der Datenbank nicht finden.")
                
        else:
            await ctx.send(f"❌ Ungültige Nummer. Du hast nur **{len(meine_aufgaben)}** Aufgaben.")
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
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # 1. Kanal suchen (wie gehabt)
        channel = guild.system_channel
        if channel is None:
            for c in guild.text_channels:
                if c.permissions_for(guild.me).send_messages:
                    channel = c
                    break
        
        if channel is None:
            return

        # 2. Begrüßung (kurz & freundlich)
        intro_text = (
            f"👋 Hi! Ich bin **{self.bot.user.name}**.\n"
            "Ich helfe euch, Deadlines im Blick zu behalten. Hier ist ein schneller Überblick, wie ich funktioniere:"
        )
        await channel.send(intro_text)

        # 3. Schnellstart-Guide als Embed
        
        beschreibung = (
            "**📝 Neue Aufgabe erstellen**\n"
            "Nutze `!neu`, Titel in Anführungszeichen, Datum und optional die Wichtigkeit (1-5).\n"
            "> Bsp: `!neu \"Mathe\" 20.05.2025 14:00 5` (5 = sehr wichtig)\n\n"
            
            "**📋 Liste anzeigen**\n"
            "Mit `!liste` (oder `!list`) siehst du alle offenen Aufgaben und wie viel Zeit noch bleibt.\n\n"
            
            "**✅ Aufgabe erledigen**\n"
            "Nutze `!fertig` (oder `!done`) und die Nummer der Aufgabe aus der Liste.\n"
            "> Bsp: `!fertig 1`\n\n"
            
            "**🗑️ Aufgabe loeschen**\n"
            "Wenn du dich vertippt hast: `!loeschen` (oder `!del`) entfernt sie, ohne Punkte/Erfolg.\n"
            "> Bsp: `!loeschen 2`\n\n"
            
            "**⏰ Zeit verschieben**\n"
            "Brauchst du mehr Zeit? Nutze `!verschieben` (oder `!delay`).\n"
            "> Bsp: `!verschieben 1 30m` (30 Min später)\n"
            "> Bsp: `!verschieben 1 1d` (1 Tag später)\n\n"
            
            "**💪 Motivation**\n"
            "Tippe `!motivation` für einen zufälligen Spruch."
            
            "**❓ Hilfe & Anleitung**\n"
            "Zeigt dir diese Übersicht erneut an: `!hilfe` (oder `!help`)"
        )

        embed = discord.Embed(
            title="🚀 Schnellstart-Guide",
            description=beschreibung,
            color=discord.Color.gold() 
        )
        
        # Fußzeile mit Datumshinweis
        embed.set_footer(text="Tipp: Datum ist immer Tag.Monat.Jahr")

        # Embed senden
        await channel.send(embed=embed)
        
    #--- HILFSFUNKTIONEN ---
    
    #Methode um Aufgaben eines Users zu bekommen
    def get_tasks_for_user(self, user_id):
        return [t for t in self.todos if t["user_id"] == user_id]


async def setup(bot):
    await bot.add_cog(Todo(bot))
