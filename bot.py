import discord
from discord import app_commands
from discord.ext import commands
import os
import requests
from anthropic import Anthropic

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GUILD_ID = discord.Object(id=995650336679276556)

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Resources embed content ----------

EMBED_TITLE = "Scam Investigator Resources"
EMBED_BODY = """
Welcome to the Scam Investigators Resources channel. Here you will find numerous resources, ranging from ticket templates to handbooks.

It is important to refresh on our resources frequently to avoid errors when handling tickets. If you require assistance, please reach out to a member of staff to avail of support.

**SI General Handbook**
[RoDevs SI Handbook](https://docs.google.com/document/d/1PbBsliamdNZlxxPD5mTKmmDsUmPhjlPU6yKGzKIrE_8/edit?usp=sharing)

**SI Ban Appeal Guide**
[RoDevs SI Ban Appeal Guide](https://docs.google.com/document/d/1A8r-GMBX8kj7o0VxhLUZ3L4bMA-llXNhSfzvqMDhcR8/edit?usp=sharing)

**SI AI-Detection Guide**
[AI Detection Guide](https://docs.google.com/document/d/10Ki9Gqc5tvnOr-l7sE1hdOxhLCnGNWwOz1-_bnsUh08/edit?tab=t.0)

It is important to ensure you stay refreshed on the above frequently.
"""

def build_embed():
    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_BODY,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Posted automatically by the bot")
    embed.timestamp = discord.utils.utcnow()
    return embed

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

TEMPLATES = {
    "opening": ("Opening Message", OPENING_MESSAGE),
    "accusing": ("Accusing the Scammer", ACCUSING_MESSAGE),
    "conclusion": ("Ticket Conclusion", CONCLUSION_MESSAGE),
    "conclusion_tips": ("Ticket Conclusion and Tips Request", CONCLUSION_TIPS_MESSAGE),
    "reopen": ("Steps to Reopen a Closed Thread", REOPEN_THREAD_MESSAGE),
}

# ---------- Handbook Q&A setup ----------

HANDBOOK_DOCS = {
    "SI General Handbook": "1PbBsliamdNZlxxPD5mTKmmDsUmPhjlPU6yKGzKIrE_8",
    "SI Ban Appeal Guide": "1A8r-GMBX8kj7o0VxhLUZ3L4bMA-llXNhSfzvqMDhcR8",
    "SI AI-Detection Guide": "10Ki9Gqc5tvnOr-l7sE1hdOxhLCnGNWwOz1-_bnsUh08",
}

handbook_text_cache = {}

def fetch_doc_text(doc_id: str) -> str:
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text

def load_handbooks():
    for name, doc_id in HANDBOOK_DOCS.items():
        try:
            handbook_text_cache[name] = fetch_doc_text(doc_id)
            print(f"Loaded handbook: {name} ({len(handbook_text_cache[name])} chars)")
        except Exception as e:
            print(f"Failed to load handbook '{name}': {e}")

def ask_claude(question: str) -> str:
    combined_docs = "\n\n".join(
        f"=== {name} ===\n{text}" for name, text in handbook_text_cache.items()
    )

    system_prompt = (
        "You are a helpful assistant answering questions for Scam Investigator staff "
        "based ONLY on the handbook content provided below. If the answer isn't in the "
        "handbooks, say so clearly rather than guessing. Keep answers concise and practical.\n\n"
        f"{combined_docs}"
    )

    response = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text

# ---------- Bot events ----------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    load_handbooks()
    try:
        bot.tree.copy_global_to(guild=GUILD_ID)
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Synced {len(synced)} slash command(s) to guild")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ---------- Slash commands ----------

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

@bot.tree.command(name="ask", description="Ask a question about the SI handbooks")
@app_commands.describe(question="What do you want to know?")
async def ask_command(interaction: discord.Interaction, question: str):
    await interaction.response.defer()  # AI call may take a few seconds
    try:
        answer = ask_claude(question)
    except Exception as e:
        await interaction.followup.send(f"Something went wrong answering that: {e}")
        return

    embed = discord.Embed(
        title="Handbook Answer",
        description=answer,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Q: {question}"[:2048])
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="updateresources", description="Edit the existing Resources message with the latest content")
@app_commands.describe(message_id="The message ID of the Resources embed to update")
@app_commands.checks.has_permissions(manage_messages=True)
async def updateresources_command(interaction: discord.Interaction, message_id: str):
    try:
        message = await interaction.channel.fetch_message(int(message_id))
        await message.edit(embed=build_embed())
        await interaction.response.send_message("Resources message updated.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Couldn't update that message: {e}", ephemeral=True)

bot.run(TOKEN)
