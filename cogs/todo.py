import discord
from discord.ext import commands, tasks
from datetime import datetime

class Todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.todos = [] # Hier werden die Aufgaben gespeichert
        self.check_deadlines.start() # Startet den Hintergrund-Check

    def cog_unload(self):
        self.check_deadlines.cancel()

    # --- COMMAND: Aufgabe hinzufügen ---
    @commands.command()
    async def add(self, ctx, task_name: str, date_str: str, time_str: str):
        """
        Fügt eine Aufgabe hinzu.
        Format: !add "Aufgaben Name" YYYY-MM-DD HH:MM
        """
        try:
            # Datum und Zeit zusammenfügen
            deadline_str = f"{date_str} {time_str}"
            # In ein echtes Zeit-Objekt umwandeln
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            
            task_entry = {
                "task": task_name,
                "deadline": deadline_dt,
                "user_id": ctx.author.id,
                "channel_id": ctx.channel.id
            }
            
            self.todos.append(task_entry)
            await ctx.send(f"✅ Aufgabe **'{task_name}'** gespeichert! Deadline: {deadline_str}")
            
        except ValueError:
            await ctx.send("❌ Falsches Format! Bitte so: `!add \"Aufgabe\" 2024-12-31 18:00`")

    # --- COMMAND: Liste anzeigen ---
    @commands.command()
    async def list(self, ctx):
        """Zeigt deine offenen Aufgaben an"""
        # Nur Aufgaben vom Nutzer holen, der den Befehl schreibt
        user_tasks = [t for t in self.todos if t["user_id"] == ctx.author.id]
        
        if not user_tasks:
            await ctx.send("Du hast keine offenen Aufgaben.")
            return

        message = "**Deine To-Do Liste:**\n"
        for i, task in enumerate(user_tasks, 1):
            fmt_time = task["deadline"].strftime("%d.%m.%Y um %H:%M Uhr")
            message += f"{i}. **{task['task']}** (Bis: {fmt_time})\n"
        
        await ctx.send(message)

    # --- HINTERGRUND TASK: Deadlines prüfen ---
    @tasks.loop(seconds=60) # Läuft jede Minute
    async def check_deadlines(self):
        now = datetime.now()
        to_remove = []

        for task in self.todos:
            # Wenn die Zeit abgelaufen ist (oder genau jetzt ist)
            if now >= task["deadline"]:
                channel = self.bot.get_channel(task["channel_id"])
                
                if channel:
                    # User pingen und benachrichtigen
                    await channel.send(f"⏰ **ALARM!** <@{task['user_id']}>: Deine Deadline für **'{task['task']}'** ist erreicht!")
                
                # Aufgabe zum Löschen markieren
                to_remove.append(task)
        
        # Erledigte Aufgaben aus der Liste werfen
        for task in to_remove:
            if task in self.todos:
                self.todos.remove(task)

    @check_deadlines.before_loop
    async def before_check(self):
        # Warten bis der Bot bereit ist, bevor der Loop startet
        await self.bot.wait_until_ready()

# Das hier ist wichtig, damit die main.py diese Datei laden kann
async def setup(bot):
    await bot.add_cog(Todo(bot))