import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = discord.Object(id=995650336679276556)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Template content ----------

OPENING_MESSAGE = """Hey there, I'm [NAME], a Scam Investigator at RoDevs. Thank you for your patience!
**Please provide the following:**
> - The ID of the accused ([Enable Developer Mode for this](https://youtu.be/9jZdxTnkEe0?si=Rb6M8pd5Odg5JOBE))
> - A full-screen video of you scrolling through the scammer's DMS slowly from top to bottom.
> - Any additional information/context you'd like to add.
- You have **24 hours** to respond until this ticket is deleted. :alarm_clock:"""

ACCUSING_MESSAGE = """:warning: __**YOU'VE BEEN ACCUSED OF [CASE]**__ :warning:
> - Victim: `<@UserId>` | User ID
> - Case: [Scamming, Free Models, Plagiarizing]
> - Reason: [What did the scammer do that broke the rules in-depth?]
> - This violates Scam Rule: [What rule does this violate in scam-prevention]?
- **Failure to respond to the accusations within the next 12 hours will result in severe punishment!** :alarm_clock:"""

CONCLUSION_MESSAGE = """**__This ticket was settled!__**
> The scammer received this punishment: `Punishment | Can it be appealed?`
> The ticket will be closed soon, so ask your questions if there are any!
**To prevent scams from happening in the future, please use services like the Middleman service RoDevs provides, make sure to read [Scam Prevention](https://discord.com/channels/601117178896580608/809404102965723166) and our [Commissions Guide](https://discord.com/channels/601117178896580608/744069939865976872/1529279371582640189).**"""

CONCLUSION_TIPS_MESSAGE = """**This ticket was settled!**
> The scammer received this punishment: `Punishment | Can it be appealed?`
> The ticket will be closed soon, so ask your questions if there are any!
**To prevent scams from happening in the future, please use services like the Middleman service RoDevs provides, make sure to read [Scam Prevention](https://discord.com/channels/601117178896580608/809404102965723166) and our [Commissions Guide](https://discord.com/channels/601117178896580608/744069939865976872/1529279371582640189).**
*If you're happy with the support provided today, feel free to show your appreciation at https://rodevs.com/donate?ctx=tip. :military_medal: Tips are never expected but always appreciated! Have a great day!*"""

REOPEN_THREAD_MESSAGE = """Your thread was most likely auto-closed and not deleted. Below are instructions on how to retrieve your thread.
**Step 1**
> Go to the channel where the thread was originally in.
**Step 2**
> Click on the threads button in the top right corner. It's the 4th button to the left. Hovering over it should say "Threads".
**Step 3**
> Doing this will show you every thread you have open in that channel. If one or more threads pop up simply find the thread of yours that you want to view and click on the box.
**Step 4**
> Once you have done this, send a message in the thread. Doing so will reopen the thread. Then, ping me in the thread so I can review the evidence.
Please let me know if you have any issues or questions doing this."""

# ---------- Template lookup ----------
TEMPLATES = {
    "opening": ("Opening Message", OPENING_MESSAGE),
    "accusing": ("Accusing the Scammer", ACCUSING_MESSAGE),
    "conclusion": ("Ticket Conclusion", CONCLUSION_MESSAGE),
    "conclusion_tips": ("Ticket Conclusion and Tips Request", CONCLUSION_TIPS_MESSAGE),
    "reopen": ("Steps to Reopen a Closed Thread", REOPEN_THREAD_MESSAGE),
}

# ---------- Slash command ----------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        bot.tree.copy_global_to(guild=GUILD_ID)
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Synced {len(synced)} slash command(s) to guild")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="templates", description="Get a Scam Investigator template message")
@app_commands.describe(template="Choose which template you need")
@app_commands.choices(template=[
    app_commands.Choice(name="Opening Message", value="opening"),
    app_commands.Choice(name="Accusing the Scammer", value="accusing"),
    app_commands.Choice(name="Ticket Conclusion", value="conclusion"),
    app_commands.Choice(name="Ticket Conclusion + Tips Request", value="conclusion_tips"),
    app_commands.Choice(name="Steps to Reopen a Closed Thread", value="reopen"),
])
async def templates_command(interaction: discord.Interaction, template: app_commands.Choice[str]):
    title, content = TEMPLATES[template.value]

    embed = discord.Embed(
        title=title,
        description=f"```\n{content}\n```",
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
