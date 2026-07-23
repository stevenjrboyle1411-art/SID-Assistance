import discord
from discord.ext import commands
import os

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
CHANNEL_ID = 1529617348644962314  # your channel ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

EMBED_TITLE = "Scam Investigator Resources"
EMBED_BODY = """
Welcome to the Scam Investigators Resources channel. Here you will find numerous resources, ranging from ticket templates to handbooks.

It is important to refresh on our resources frequently to avoid errors when handling tickets. If you require assistance, please reach out to a member of staff to avail of support.

**SI General Handbook**
[RoDevs SI Handbook](https://docs.google.com/document/d/1PbBsliamdNZlxxPD5mTKmmDsUmPhjlPU6yKGzKIrE_8/edit?usp=sharing)

**SI Ban Appeal Guide**
[RoDevs SI Ban Appeal Guide](https://docs.google.com/document/d/1A8r-GMBX8kj7o0VxhLUZ3L4bMA-llXNhSfzvqMDhcR8/edit?usp=sharing)

**SI AI-Detection Guide**
[AI Detection Guide](https://docs.google.com/document/d/1PbBsliamdNZlxxPD5mTKmmDsUmPhjlPU6yKGzKIrE_8/edit?usp=sharing)

It is important to ensure you stay refreshed on the above frequently.
"""

TEMPLATES_TITLE = "Scam Investigator Template Messages"

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

TEMPLATES_BODY = (
    "**Opening Message**\n```\n" + OPENING_MESSAGE + "\n```\n\n"
    "**Accusing the Scammer**\n```\n" + ACCUSING_MESSAGE + "\n```\n\n"
    "**Ticket Conclusion**\n```\n" + CONCLUSION_MESSAGE + "\n```\n\n"
    "**Ticket Conclusion and Tips Request**\n```\n" + CONCLUSION_TIPS_MESSAGE + "\n```\n\n"
    "**Steps to Reopen a Closed Thread**\n```\n" + REOPEN_THREAD_MESSAGE + "\n```"
)

def build_embed():
    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_BODY,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Posted automatically by the bot")
    embed.timestamp = discord.utils.utcnow()
    return embed

def build_templates_embed():
    embed = discord.Embed(
        title=TEMPLATES_TITLE,
        description=TEMPLATES_BODY,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="SIDA")
    embed.timestamp = discord.utils.utcnow()
    return embed

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(embed=build_templates_embed())
    await channel.send(embed=build_embed())

bot.run(TOKEN)
