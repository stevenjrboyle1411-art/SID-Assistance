import discord
from discord import app_commands
from discord.ext import commands
import os
import base64
import re
import subprocess
import tempfile
import asyncio
from openai import OpenAI

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GUILD_ID = discord.Object(id=995650336679276556)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Role-based access control (per-server) ----------

ALLOWED_ROLES_BY_GUILD = {
    995650336679276556: {995663617112416296, 995664357801345044},
    1513911328807456778: {1529974721448513556},
}

def has_allowed_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild_id not in ALLOWED_ROLES_BY_GUILD:
            # Server not configured with a role list — deny by default for safety
            return False

        allowed_role_ids = ALLOWED_ROLES_BY_GUILD[interaction.guild_id]
        member_role_ids = {role.id for role in interaction.user.roles}

        if allowed_role_ids.isdisjoint(member_role_ids):
            raise app_commands.CheckFailure(
                "You don't have a role permitted to use this command."
            )
        return True
    return app_commands.check(predicate)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        message = "You don't have permission to use this command."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    else:
        raise error

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

# ---------- Handbook Q&A setup (static text, no Google dependency) ----------

HANDBOOK_TEXT = """Created for the RoDevs Scam Investigation Department
This handbook explains roles, ticket handling, evidence standards, logging, punishments, escalation, and department discipline.

Possession of this document comes with the strict responsibility to maintain its confidentiality. Any individual found leaking or sharing the contents of this document will be permanently blacklisted from RoDevs.


Have a Question?
Do not hesitate to ask for clarification. Asking questions is encouraged and demonstrates a commitment to learning. You may reach out to a fellow Scam Investigator or a Senior Scam Investigator/HSI for assistance.


At a glance
Read every ticket carefully, stay neutral, use video evidence whenever possible, follow chain of command, and never punish without the required permission if you are still training.


Quick Reference
Topic
Rule
Training
TSIs need permission from a Trainer or SSI before working tickets.
Punishment authority
SIs can punish independently. TSIs cannot.
Evidence
Video evidence is preferred and often required for review.
Private staff notes
Use $$ in ticket messages so victims/accused cannot see them.
Logging
Use approved hosts such as YouTube, Google Drive, or Imgur.
Naming
Rename logs to Scam Log [Ticket Number].


1. Introduction

SI Code Of Conduct
Take your time to investigate every ticket thoroughly and ensure the scammer is correctly reprimanded. One common issue within the department is ticket-sniping, where scam investigators (mainly trials) rush tickets and end up making mistakes. It's better to take your time and do it well than rush and make mistakes just for higher numbers. Those who take their time are rewarded more than those who rush due to the high quality of their investigation.
Always be professional in tickets, you must not show any bias or be immature as this can give a bad image to the department.
Be respectful to your peers and other staff members. You are not above anyone; treat others how you want to be treated.
DO NOT leak anything, this can be a scam investigator guide, chats from the staff server etc. If found leaking, you will face the consequences.
If you are reading this handbook, you have already cleared an important first step. Scam Investigation is not just about catching bad behavior. It is about protecting the community, making fair decisions, and keeping your work consistent enough that other staff can trust your judgment.
The biggest difference between a good investigator and a rushed one is discipline. Good investigators slow down long enough to understand the report, compare evidence, ask the right questions, and make decisions that are defensible later. This handbook is designed to give you that structure.

Department mindset
Be calm, neutral, and methodical. Your job is not to "win" an argument. Your job is to find out what actually happened and investigate it properly.

2. Roles and Responsibilities
The department is organized so that each rank has a clear purpose. That makes the workflow faster, keeps training consistent, and prevents investigators from overstepping into decisions they are not supposed to make.
Role
Main purpose
What they can do
What they should avoid
Trial Scam Investigator (TSI)
Learn the process
Review tickets with approval, ask questions, practice investigations
Punishing without permission, working outside guidance
Scam Investigator (SI)
Handle day-to-day cases
Investigate independently, speak to users, issue punishments
Ignoring neutrality, skipping evidence checks
Senior Scam Investigator (SSI)
Oversee quality
Handle escalations, support training, issue disciplinary actions, review difficult cases, assist the HSI
Micromanaging routine tickets unnecessarily
Head Scam Investigator (HSI)
Lead the department
Set final direction, resolve major disputes, oversee staff decisions
Getting pulled into routine cases too early


TSIs are in the learning stage. They should expect to ask a lot of questions and should never treat that as a weakness. Questions are how you learn the standards before they become habits. SIs are expected to move more independently, but independence still comes with the same expectations for fairness, evidence quality, and professionalism. SSIs and HSIs exist to keep the department aligned and to resolve cases that are too sensitive, too complex, or too escalated for a lower rank to handle cleanly.
3. Chain of Command
The chain of command keeps communication efficient and avoids unnecessary escalation.
Order
Rank
1
Trial Scam Investigator
2
Scam Investigator
3
Senior Scam Investigator
4
Head Scam Investigator
5
Administrator


When you need help, contact the lowest rank above you that can realistically solve the problem. Do not skip rank levels unless the proper person is unavailable. The point is to keep workload organized and to make sure decisions are made by the right people.
4. Getting Started
Before touching any ticket, get approval from your Trainer or an available SSI if you are still a TSI. That permission step matters because it confirms that someone above you knows you are actively training and gives them a chance to steer you before mistakes become habits.
Open the ticket and read the full report before typing anything.
Identify the type of scam or issue being reported.
Check whether the case is clearly yours to handle or should be escalated.
Gather the evidence first, then decide on next steps.
Keep your messages respectful and focused on facts.
5. Understanding Tickets and Cases
Every ticket has a structure for a reason. The reporter, their original message, the target, the target's region or timezone, and the reported scam type are not random details. They tell you who is involved, what happened, and how the case should be approached.
Read this part carefully
The first mistake many new investigators make is reacting too quickly to the first message they see. Always read the full ticket context before claiming ownership or asking the accused to respond.


Ticket element
Why it matters
Reporter
Shows who is claiming harm and may need follow-up questions.
Original message
Contains the original allegation and usually the strongest starting context.
Target
Tells you who is accused and who may need to be added to the ticket.
Region/timezone
Helps you understand response windows and timing.
Scam type
Directs you toward the right investigation workflow.
Evidence links
Tells you whether the report has usable supporting material.



If you need to message other staff inside the ticket, use $$ before the message so the victim and accused cannot read it. That keeps internal notes private and prevents confusion or unnecessary escalation inside the case. Always maintain proper grammar across all cases.
6. Evidence Standards
Evidence quality is one of the most important parts of the department. In most cases, video evidence is the safest standard because screenshots can be cropped, edited, or taken out of context.
Ask for full-screen recordings of the full DMs or the scam. You're looking for the original deal, the payment agreement and the scam.
Ask for a page reload as well as them showing their extensions at the start of the video if evidence comes from the Discord web version.
Request external uploads to YouTube, Drive, or Dropbox if the file is too large for Discord.
Treat missing or incomplete evidence carefully. Do not guess.
Use image searches and verification tools when checking marketplace assets.

Important
If a report cannot be supported with usable evidence and the user cannot provide what is needed, drop the report rather than forcing a weak decision.

7. Investigating Marketplace Scams and Ghost Tickets
Marketplace scams are cases involving selling stolen, free, AI-generated, plagiarized, or otherwise misrepresented work, or using them in posts. These reports often appear as ghost tickets, meaning the report was created automatically from a post rather than manually created by a victim.
Run a background check on the accused so you understand prior behavior and possible patterns.
Review the post or work example and try to locate the original source using reverse search tools.
If the original cannot be found, add the reporter to the ticket and ask them for the missing link.
If the reporter cannot provide a usable source, drop the report rather than guessing.
Once you have strong evidence, add the accused user to the ticket.
Ask the accused to prove ownership or legitimate rights to the asset.
If they prove ownership, drop the report. If they cannot, continue toward resolution or punishment.

Tool / action
Purpose
/background-check
See scam logs
Yandex reverse image search
Good for finding copied artwork, stolen previews, and alternate sources.
TinEye
Strong for exact and near-exact image matches and older copies.
Google reverse image search
Useful for broad web matches, visually similar results, and alternate indexing.
SynthID via Gemini
Used to check whether an image was made by Google AI tools.
SightEngine / AI image detectors
Detecting if an image has been AI generated.


When someone is accused of using stolen work, the key question is not whether the work looks impressive. The real question is whether they had the right to present it as theirs. Ask for creation proof, purchase proof with resale rights, or any other evidence that actually proves legitimate ownership.
Subtopic: Investigating AI-Generated Work
What to look for in images and GFX
· Conflicting shadows or lighting that do not match the same scene.
· Asymmetry where symmetry should exist, like uneven eyes, ears, hands, or clothing edges.
· Hand and finger errors, merged fingers, extra fingers, or unnatural bends.
· Glossy, over-smoothed, or oddly painterly AI-looking surfaces.
· Background objects floating, warping, or failing to connect naturally to the scene.
· Repeated textures, warped text, strange logos, or details that look copied from a generator rather than drawn by hand.

What to look for in 3D models and assets
· Chaotic geometry or pointless surface noise on edges, tips, and corners.
· Objects that should be symmetrical but are subtly different on each side.
· Merged parts that should be separate, such as a blade fused into the hilt or a barrel fused into the frame.
· Non-functional details like solid triggers, fake barrel openings, or broken joints.
· Lumpy edge terminations, warped circles, uneven spokes, and poor topology.
· Textures or materials that do not match the shape and quality of the mesh.

Topology note: Poor topology, broken geometry, and unnatural mesh structure are strong clues when checking whether a model may have been AI-generated or heavily auto-produced.

What to look for in scripts
· Very generic function and variable names that feel template-like.
· Unnatural or overly robotic comments in places where a human normally would not comment so much.
· A script structure that feels too polished, repetitive, or boilerplate-heavy without real project context.
· Missing signs of natural iteration, such as consistent naming changes, edit history, or believable development flow.

SynthID specifically
SynthID is Google DeepMind's invisible watermarking system for images produced by Google AI tools such as Gemini or Imagen. It is useful, but it is not universal. A positive SynthID result means that the image was generated with SynthID.
· Open Gemini and upload the image.
· Ask directly whether the image has a SynthID watermark.
· Treat detected SynthID as evidence that the image came from Google AI tools.
· Treat not detected or uncertain as incomplete, not as proof that the work is human-made.

Key rule: No tool should be treated as absolute proof on its own. Use the tool result alongside visual cues, source tracing, and ownership proof.

What to request from the accused
· Original project files such as .blend, .psd, or similar source files.
· Version history, timestamps, or creation proof of script creation/model creation.
· Sketches, drafts, or work-in-progress files.
· Receipts or licenses if they bought the asset legally.
· A clear explanation of where the asset came from and why they had the right to use it.
8. Investigating Time-Wasting, Ghosting, Blocking, and Deal Changes
Time-wasting cases are usually commission disputes. One party agrees to a deal and then breaks it in a way that harms the other party's time, money, or work output. Sometimes the developer never finishes. Sometimes the client fails to pay. Sometimes one party changes the deal without permission. Sometimes someone blocks the other person to escape the agreement.
These cases should be handled with a strong effort to understand the full situation before punishing anyone. A good investigation in this category often starts with the simplest question: can this be resolved by refund or compromise first?
Ask for the accused's Discord User ID if needed so you can add them to the ticket.
Request evidence of the original agreement.
Request evidence of the transaction or payment flow.
Request evidence of the actual scam or failure to deliver.
Verify the evidence in full-screen video format whenever possible.
Check whether the story matches the timestamps and messages.
Run background checks
Add the accused to the ticket and allow the response window.

Practical goal
Try to resolve the issue through refund or compromise before moving directly to punishment whenever the facts support that approach.


If the accused responds, keep the discussion steady and factual. Ask them to explain missing details. Compare both sides against the evidence & make your verdict on the case. If the refund happens, a warning or no punishment may be appropriate depending on the circumstances. If the user refuses to respond after the response window, you may proceed according to department rules.

If the accused doesn't comply, please proceed to punishments below.

Communication with Accused Scammer:

Add the accused scammer to the ticket and provide a 12-24 hour response deadline.
Request video evidence to support their explanation.
Evaluate common explanations:
Hospital visit: Lower punishment consideration.
School: Consider the time wasted and lower punishment if it's like exam period, May-June.
Not enough time: Determine an acceptable extension if the victim wants.
Vacation: Consider the time wasted and lower punishment
Not enough money: Set a payment deadline or estimate.
Work was too hard: Negotiate a partial refund or full refund.
Distrust of the other party: Suggest a middleman.
Work quality issues: Evaluate work against provided references.
No explanation: Apply appropriate penalties.


9. How to Investigate Without Losing Neutrality
Use common sense, but do not rely on intuition alone.
Ask clear follow-up questions instead of assuming the answer.
Compare what each side says against the evidence line by line.
Pay attention to timestamps, delivery promises, payment status, and changes in agreement terms.
Stay professional even if one side is rude or defensive.
Remember that a loud story is not the same as a true story.

Neutrality is not passive behavior. It means you are actively checking both sides with the same standards. You are not there to protect the first person who speaks. You are there to verify what happened.

Asking Effective Questions:
Incorporate open-ended questions to uncover the reasoning behind actions.
Avoid judgmental language or phrasing to encourage complete information disclosure, judgemental language would risk alienating the scammer and compromise possible resolutions.
Frame questions neutrally. For instance, "What were your initial thoughts when they requested your password?" instead of "Weren't you suspicious when they asked for your password?".
Explore different perspectives without appearing biased.
Ensure questioning does not favor the scammer's viewpoint or unduly scrutinize the victim.
Focus on understanding all facets of the situation from a neutral standpoint.
Focus on open-ended inquiries about motivations and maintain a neutral, non-judgmental stance to foster information sharing.
Gain a deeper understanding of the dynamics at play in scam investigations.
For all screenshots sent out of context, request context behind them and the other side's opinion, and request videos or extra evidence if needed.
Understand everything to work out a resolution or make a coherent decision.
Ensure you gather enough information from both sides, including their opinions on each other's evidence, to come to a fair resolution.
Punish inconsistencies in arguments effectively by refuting.

10. Logging a Ticket
Once a case is concluded, the log has to be clear enough that another staff member can understand the decision later without needing to re-investigate from scratch.
Logging rule
What to do
Approved hosts
Use YouTube, Google Drive, or Imgur for final evidence storage.
Naming convention
Rename the video file to Scam Log [Ticket Number].
Visibility
Use Unlisted, Hidden, or appropriate sharing settings so the log is accessible but controlled.
Evidence type
Keep the primary evidence in video format whenever possible.
Screenshots
Capture images from the video later if needed for a log album or archive.

If a user cannot upload a video because of Discord's upload limit, request an external host such as YouTube, Google Drive, or another approved platform. The goal is not convenience alone. The goal is traceability and verification.

Punishment Requests, Temporary Timewasting bans, and Marketplace punishments are NOT to be uploaded to HD. Only upload permanent timewasting bans to HD.

Demonstration: https://youtu.be/7WukB248sLE?si=b8PTN3R2K4jQ2OeS
Tutorial on Blurring: https://youtu.be/BUCQ3skYqyA?si=SLEG7Z7RZBYWwk8O

Blurring note
If your department says blurring is optional now, keep it optional. When blur is used anyway, focus on real personal data such as names, emails, payment-service usernames, addresses, phone numbers, card information.

11. Punishments and Outcome Scaling
Punishment should match the situation. Not every case is the same, and not every case should end the same way. Severity depends on the scam type, whether the user refunded, whether the case was malicious, and whether there is history showing a pattern.
Case type
Typical outcome
Time-wasting, ghosting, refusal to refund
Permanent ban, appeal possible once the victim is refunded or paid.
Refund made after investigation
Warning or no punishment depending on context
Stolen assets, free models, fake reviews, plagiarism
60 to 90 day temporary ban, second offense becomes permanent
Developer fails to complete work and no payment was sent
Use discretionary scaling based on duration and severity
Developer fails to complete work and no payment was sent.
Suggested response
1 to 2 days
Warning
3 to 7 days
5 to 7 day ban
7 to 14 days
14 to 21 day ban
14 to 30 days
3 to 6 month ban
30+ days
Permanent ban

This scaling is discretionary, not automatic. You still need to look at the context.

We do NOT do Marketplace (MP) Bans anymore.
12. Reporting and Escalation
Escalations are for difficult, sensitive, or conflict-heavy situations. If a user in the report asks for the case to be elevated to an SSI, follow that instruction. If the report involves you personally or involves a close friend, step back and let someone else handle it.
Do not investigate your own report.
Do not force yourself into a case where bias could be questioned.
Use senior staff when the conflict is personal, unusual, or disputed.
Escalate when a report needs authority beyond your rank.
13. Mistakes, Strikes, and Discipline
The department uses discipline to keep standards consistent. Mistakes are typically issues that need correction and time-based tracking. Strikes are more serious and usually point to broader reliability or behavior concerns. SSI+ can issue disciplinary actions.
Mistake
Duration / note
Leaving a ticket inactive or not logging for too long
Usually lasts 30 days
Grammar errors in tickets
Usually lasts 30 days
Missing scam investigation meetings without a valid reason
Lasts until the next meeting
Missing quota
Usually lasts 14 days
Repeated denied logs from HD
Usually lasts 30 days
Strike reason
Typical consequence
Too many mistakes
Retraining, usually lasting 30 days
Low engagement or inactivity
30 day consequence
Negative behavior or toxicity
30 day consequence
Abusing the inactivity system
30 day consequence
Talking negatively about the department after warning
30 day consequence
Small amounts of bias in tickets or appeals
60 day consequence
Missing quota repeatedly or abusing quota
28 day consequence
Banning someone in error and failing to correct it
30 day consequence


Demotions Triggers
Common demotion triggers include too many strikes(3+), leaking staff information, taking bribes or incentives, and repeated bias in cases.


14. Resources and Formats
The department relies on a number of tools for review, verification, background checks, and documentation. You do not need to memorize every tool on day one, but you should know what kinds of problems each category of tool solves.
Resource
Use
RoDevs Commission Guide
Tips & Tricks for commissions as well as Do & Don'ts
HD Scam Logs
Background checks
RIA Scam Logs
Background checks
VirusTotal
Scanner for viruses in links & files
Grammarly
Grammar correction
EzGif Video Reverser
Reversing videos
EzGif Video Slower
Slowing down video
Roblox Leaked Games
For stolen work detection
Yandex
Reverse searching, stolen work detection
TinEye
Reverse searching, stolen work detection
Google Reverse Image Search
Reverse searching, stolen work detection
SightEngine
Detecting AI-generated work
SynthID
Common Scam Portfolios
Topology guides for detecting AI-generated models
cobalt
Video downloader
CnvMP3
YouTube downloader



Use the resources responsibly. Some tools are for internal staff use only and should not be shared carelessly. The point of the tool list is to ease your workload.

Misc:
Banning Compromised Accounts
Compromised accounts will be fairly obvious to spot, and will send an image relating to a Mr Beast twitter post, or an Elon Musk twitter post, with 4 images explaining "steps" to claim free money. You must only do this on accounts that are clearly compromised!

This is the only time you can issue punishments for something outside of the Scam Investigator guidelines. Scam Investigators must not interfere in punishments outside of compromised accounts and bans correlating from scams no matter the situation. You must ping a moderator for cases outside of the above.
*Exception for NSFW in VCs per announcement.


If you come across this in server channels, you should remove the user immediately.
To do so, follow the below steps
- Right click the message
- Select apps
- Select RoDevs
- Select " Compromised Account "

This will ban the user for one minute and send them a message explaining why, and an invite to rejoin the server. All departments have the ability to do this. If you are confused, please ping a moderator in staff-chat. If you are found misusing this, punishment will follow.

Formats:
Formats exist to make your life easier and to provide you with a foundation from which you can conduct operations. All the formats in the SI department are located in the resources & open-resources channels.

15. Frequently Asked Questions
Q: What should I do if I do not understand a ticket?
A: Ask questions early. It is better to clarify the case before acting than to clean up a wrong decision later.
Q: What if the accused claims they own the asset?
A: Ask for proof. Do not accept a claim without evidence.
Q: What if the victim cannot provide full video evidence?
A: Request an external upload. If usable evidence still cannot be provided, drop the report.
Q: What if both sides are partly wrong?
A: Use judgment. Sometimes a warning, compromise, or case drop is more appropriate than a harsh punishment.
Q: What if the case is personal or involves a friend?
A: Step aside and let someone else handle it.
Q: What do I do if my scam log gets denied?
A: Inform an SSI to talk to HD. Never contact HD staff directly unless given permission by a DH+.
Q: Why can't I delete my appeal?
A: For deleting a ban appeal once logged, you would hit the 'Delete Ticket' button at the top, then when it prompts you, click Delete again.
Q: How do I log PR ban appeals?
A: Currently, PR ban appeals can't be logged through the bot, so ping an SSI to log it manually for you.
Q: Do you use /scam create on PRs?
A: No, just ban and accept the punishment request.
Q: What do I do if the accused isn't in the server?
A: If the accused scammer isn't in the server and the evidence is sufficient, you can punish them outright.
Q: What do I do if the victim isn't in the server?
A: Drop the investigation.
Q: What do I do when someone makes a report on someone else's behalf?
A: If someone reports someone else on their behalf, we do not take the report unless the victim explicitly gave them permission to do so.
Q: Why can't I delete my ticket?
A: Currently, tickets have a prevailing issue regarding deletion, so ping the Head Scam Investigator to manually delete the ticket for you.
Q: What do I do if there are racial slurs in the ticket?
A: Conclude the ticket normally then transfer it to moderation department.

16. Policies & Changes!
Departmental Order #001 - 12/25/25: Updating Senior Guidelines [Effective]
Departmental Order #002 - 2/9/26: Blurring requirement rescinded; now optional. [Effective]
Departmental Order #003 - 2/28/26: Implementation of SynthID for images generated with Gemini. [Effective]
Departmental Order #004 - 3/23/26: Depreciation of old handbook & rollout of this document. [Effective]
Departmental Order #005 - 3/23/26: Reorganization of quota from a bi-weekly basis to a monthly basis. [Effective]
Departmental Order #005 -3/31/26: Rescission of the cherry-picking rule. [Effective]
17. Final Notes and Acknowledgment
The best investigators are not the fastest ones. They are the ones who are consistent, calm, and fair even when the case is annoying or the people involved are difficult. If you follow the handbook, keep your evidence clean, and ask for help when needed, you will improve quickly.
"""

def is_genuine_question(question: str) -> bool:
    """Cheap, fast check to filter out troll/nonsense/off-topic questions
    before spending tokens on the expensive model."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_completion_tokens=20,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a filter for a Scam Investigator handbook assistant. "
                        "Reply with ONLY one word, exactly YES or NO, no punctuation, "
                        "no explanation. Reply YES if the message is a genuine, "
                        "reasonable question that could plausibly relate to scam "
                        "investigation, tickets, evidence, punishments, or department "
                        "process. Reply NO only if it is clearly trolling, spam, an "
                        "insult, or has nothing at all to do with the department. "
                        "When in doubt, reply YES."
                    )
                },
                {"role": "user", "content": question}
            ]
        )
        verdict = (response.choices[0].message.content or "").strip().upper()
        return "NO" not in verdict
    except Exception:
        # If the filter itself fails, default to allowing the question through
        return True

def ask_ai(question: str) -> str:
    system_prompt = (
        "You are a knowledgeable, thorough assistant answering questions for Scam "
        "Investigator staff, based ONLY on the handbook content provided below. "
        "Give detailed, well-explained answers, don't just state the rule, explain "
        "the reasoning behind it and mention relevant context from the handbook. "
        "Use headers and bullet points where they help clarity. "
        "IMPORTANT LENGTH LIMIT: your entire answer must fit within roughly 2 pages "
        "(around 500-700 words maximum). Do not exceed this. Be thorough but concise, "
        "prioritize the most important and directly relevant information rather than "
        "covering every possible angle. If the answer isn't in the handbook, say so "
        "clearly rather than guessing.\n\n"
        f"=== SI General Handbook ===\n{HANDBOOK_TEXT}"
    )

    response = openai_client.chat.completions.create(
        model="gpt-5.6-luna",
        max_completion_tokens=2500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        return (
            "I wasn't able to generate a full answer for that one, it may have been "
            "too complex for the current response limit. Try breaking your question "
            "into smaller, more specific parts."
        )
    return content

# ---------- Bot events ----------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        bot.tree.copy_global_to(guild=GUILD_ID)
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Synced {len(synced)} slash command(s) to guild")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ---------- Slash commands ----------

@bot.tree.command(name="templates", description="Get a Scam Investigator template message")
@has_allowed_role()
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
@has_allowed_role()
@app_commands.describe(question="What do you want to know?")
async def ask_command(interaction: discord.Interaction, question: str):
    await interaction.response.defer()  # AI call may take a few seconds

    if not is_genuine_question(question):
        await interaction.followup.send(
            "That doesn't look like a genuine handbook question, so I'm skipping it to save tokens. "
            "If it was real, try rephrasing it more clearly.",
            ephemeral=True
        )
        return

    try:
        answer = ask_ai(question)
    except Exception as e:
        await interaction.followup.send(f"Something went wrong answering that: {e}")
        return

    # Hard cap: never send more than 2 "pages" worth of content, no matter what the model returns
    chunk_size = 4000
    max_chunks = 2
    chunks = [answer[i:i + chunk_size] for i in range(0, len(answer), chunk_size)] or [""]
    if len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        chunks[-1] = chunks[-1][:chunk_size - 60] + "\n\n*(Response truncated to fit the 2-page limit.)*"

    first_embed = discord.Embed(
        title="Handbook Answer",
        description=chunks[0],
        color=discord.Color.blurple()
    )
    first_embed.set_footer(text=f"Q: {question}"[:2048])
    await interaction.followup.send(embed=first_embed)

    for chunk in chunks[1:]:
        follow_embed = discord.Embed(
            description=chunk,
            color=discord.Color.blurple()
        )
        await interaction.followup.send(embed=follow_embed)

@bot.tree.command(name="updateresources", description="Edit the existing Resources message with the latest content")
@has_allowed_role()
@app_commands.describe(message_id="The message ID of the Resources embed to update")
@app_commands.checks.has_permissions(manage_messages=True)
async def updateresources_command(interaction: discord.Interaction, message_id: str):
    try:
        message = await interaction.channel.fetch_message(int(message_id))
        await message.edit(embed=build_embed())
        await interaction.response.send_message("Resources message updated.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Couldn't update that message: {e}", ephemeral=True)

# ---------- Video investigation pipeline ----------

MAX_FRAMES = 60  # hard cap so a very long video doesn't run away with cost/time

def download_video(url: str, dest_dir: str) -> str:
    """Downloads a video from virtually any link (YouTube, Drive, Discord CDN,
    direct .mp4 links, etc.) using yt-dlp, which handles the vast majority of
    hosting sites via its generic + site-specific extractors."""
    output_template = os.path.join(dest_dir, "input.%(ext)s")
    cmd = ["yt-dlp", "-f", "mp4/best", "--remote-components", "ejs:github", "-o", output_template]

    # If cookies were provided via env var, write them to a temp file and use them.
    # This is often required for YouTube, which blocks anonymous cloud-server requests.
    ytdlp_cookies = os.environ.get("YTDLP_COOKIES")
    if ytdlp_cookies:
        cookies_path = os.path.join(dest_dir, "cookies.txt")
        with open(cookies_path, "w") as f:
            f.write(ytdlp_cookies)
        cmd += ["--cookies", cookies_path]

    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[-1000:]}")

    for f in os.listdir(dest_dir):
        if f.startswith("input."):
            return os.path.join(dest_dir, f)
    raise RuntimeError("Video download completed but no output file was found.")

def extract_keyframes(video_path: str, out_dir: str):
    """Extracts frames two ways and merges them:
    1. Scene-change detection (catches moments where content visibly changes)
    2. Periodic sampling every 4 seconds (a safety net in case scene detection
       misses gradual/slow scrolling, which can happen with compressed video)
    This dual approach is more reliable than scene detection alone."""

    scene_log = os.path.join(out_dir, "scene.log")
    scene_pattern = os.path.join(out_dir, "scene_%04d.png")
    cmd_scene = [
        "ffmpeg", "-i", video_path,
        "-vf", "select='gt(scene,0.15)',showinfo",
        "-vsync", "vfr",
        scene_pattern
    ]
    with open(scene_log, "w") as log_file:
        subprocess.run(cmd_scene, stdout=log_file, stderr=subprocess.STDOUT, timeout=900)

    scene_timestamps = []
    with open(scene_log, "r", errors="ignore") as f:
        for line in f:
            match = re.search(r"pts_time:(\d+\.?\d*)", line)
            if match:
                scene_timestamps.append(float(match.group(1)))

    scene_files = sorted(f for f in os.listdir(out_dir) if f.startswith("scene_"))
    scene_frames = list(zip(scene_timestamps, scene_files))
    print(f"[extract_keyframes] scene-detection found {len(scene_frames)} frames")

    # Periodic fallback: one frame every 4 seconds across the whole video
    periodic_pattern = os.path.join(out_dir, "periodic_%04d.png")
    cmd_periodic = [
        "ffmpeg", "-i", video_path,
        "-vf", "fps=1/4",
        periodic_pattern
    ]
    subprocess.run(cmd_periodic, capture_output=True, timeout=900)
    periodic_files = sorted(f for f in os.listdir(out_dir) if f.startswith("periodic_"))
    periodic_frames = [(i * 4.0, fname) for i, fname in enumerate(periodic_files)]
    print(f"[extract_keyframes] periodic sampling found {len(periodic_frames)} frames")

    all_frames = scene_frames + periodic_frames
    all_frames.sort(key=lambda x: x[0])

    # Deduplicate frames that landed within 1.5s of each other
    deduped = []
    last_ts = -999
    for ts, fname in all_frames:
        if ts - last_ts >= 1.5:
            deduped.append((ts, fname))
            last_ts = ts

    print(f"[extract_keyframes] {len(deduped)} frames after merging + deduping")

    # Cap total frames evenly across the video if there are too many
    if len(deduped) > MAX_FRAMES:
        step = len(deduped) / MAX_FRAMES
        deduped = [deduped[int(i * step)] for i in range(MAX_FRAMES)]
        print(f"[extract_keyframes] capped down to {len(deduped)} frames")

    return [(ts, os.path.join(out_dir, fname)) for ts, fname in deduped]

def format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def read_frame_text(image_path: str, timestamp_label: str) -> str:
    """Sends a single frame to a vision-capable model and asks it to transcribe
    everything visible: chat messages, usernames, and anything relevant."""
    with open(image_path, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        max_completion_tokens=500,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are transcribing a frame from a screen recording of a Discord "
                    "conversation, being reviewed as scam evidence. Transcribe ALL visible "
                    "text exactly: usernames, message content, prices, payment details, "
                    "timestamps shown on-screen. If nothing new or relevant is visible "
                    "(e.g. blank/transition frame), say 'No new content.' Be concise but complete."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Frame at video timestamp {timestamp_label}:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content or ""

class VideoUnreadableError(Exception):
    """Raised when no usable content could be extracted from a video."""
    pass

async def analyze_video(url: str, status_callback=None) -> str:
    """Full pipeline: download -> extract keyframes -> read each frame ->
    compile timeline -> generate a scam investigator case breakdown."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        if status_callback:
            await status_callback("Downloading video...")
        video_path = await asyncio.to_thread(download_video, url, tmp_dir)

        if status_callback:
            await status_callback("Scanning for key moments...")
        frames = await asyncio.to_thread(extract_keyframes, video_path, tmp_dir)

        if not frames:
            return "I couldn't extract any usable frames from that video. Please check the link or try a different upload."

        if status_callback:
            await status_callback(f"Reading {len(frames)} key moments from the video...")

        # Limit concurrent vision calls to avoid rate limits
        semaphore = asyncio.Semaphore(5)

        frame_errors = []

        async def process_frame(ts, path):
            async with semaphore:
                label = format_timestamp(ts)
                try:
                    text = await asyncio.to_thread(read_frame_text, path, label)
                except Exception as e:
                    print(f"[process_frame] error on frame at {label}: {e}")
                    frame_errors.append(f"{label}: {e}")
                    text = ""
                print(f"[process_frame] {label}: {len(text)} chars -> {text[:80]!r}")
                return ts, label, text

        results = await asyncio.gather(*[process_frame(ts, path) for ts, path in frames])
        results.sort(key=lambda r: r[0])

        timeline_lines = []
        for ts, label, text in results:
            if text.strip() and "no new content" not in text.lower():
                timeline_lines.append(f"[{label}] {text.strip()}")

        if not timeline_lines:
            if frame_errors:
                sample = " | ".join(frame_errors[:3])
                raise VideoUnreadableError(
                    f"All {len(frames)} frames failed with errors. Sample: {sample}"
                )
            else:
                raise VideoUnreadableError(
                    f"No readable content extracted from {len(frames)} frames (all frames "
                    f"returned empty or 'no new content', no API errors)."
                )

        timeline = "\n\n".join(timeline_lines)

        if status_callback:
            await status_callback("Writing the case breakdown...")

        system_prompt = (
            "You are an experienced Scam Investigator writing a full case breakdown, "
            "based on a timestamped timeline transcribed from a victim's evidence video "
            "(a screen recording of their DMs with the accused). You also have the "
            "department's handbook for reference.\n\n"
            "Write a detailed breakdown that includes:\n"
            "1. A summary of what happened, in order.\n"
            "2. Specific timestamps (MM:SS) of key moments worth reviewing, with a short "
            "note on why each matters.\n"
            "3. An assessment of whether this fits a scam/rule violation per the handbook, "
            "and which category (e.g. time-wasting, stolen assets, ghosting, etc.).\n"
            "4. A recommended punishment, using the handbook's punishment scaling as the basis.\n\n"
            f"=== SI General Handbook ===\n{HANDBOOK_TEXT}\n\n"
            f"=== Video Timeline ===\n{timeline}"
        )

        response = openai_client.chat.completions.create(
            model="gpt-5.6-luna",
            max_completion_tokens=3000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please write the full case breakdown."}
            ]
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            return "I processed the video but couldn't generate a breakdown. Try again, or the video may be too long/complex for one pass."
        return content

ERROR_LOG_CHANNEL_ID = 1166202561846583416

FRIENDLY_ERROR_MESSAGE = (
    "Sadly, I was unable to read this video. This error has been logged and will be "
    "reviewed manually to see where I went wrong. Please retry, if I continue to error, "
    "I suggest watching the video manually. Very sorry!"
)

async def log_error_to_channel(video_link: str, error: Exception, user: discord.User):
    try:
        log_channel = bot.get_channel(ERROR_LOG_CHANNEL_ID) or await bot.fetch_channel(ERROR_LOG_CHANNEL_ID)
    except Exception as e:
        print(f"[log_error_to_channel] Could not fetch log channel {ERROR_LOG_CHANNEL_ID}: {e}")
        return

    embed = discord.Embed(
        title="/investigate failure",
        color=discord.Color.red()
    )
    embed.add_field(name="Requested by", value=str(user), inline=False)
    embed.add_field(name="Video link", value=video_link[:1000], inline=False)
    embed.add_field(name="Error", value=str(error)[:1000], inline=False)
    embed.timestamp = discord.utils.utcnow()
    try:
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f"[log_error_to_channel] Failed to send log: {e}")

@bot.tree.command(name="investigate", description="Analyze a scam evidence video and get a full case breakdown")
@has_allowed_role()
@app_commands.describe(video_link="Link to the evidence video (YouTube, Drive, direct link, etc.)")
async def investigate_command(interaction: discord.Interaction, video_link: str):
    await interaction.response.defer()

    status_message = await interaction.followup.send("Starting video analysis...", wait=True)

    async def update_status(text: str):
        try:
            await status_message.edit(content=text)
        except Exception:
            pass

    try:
        breakdown = await analyze_video(video_link, status_callback=update_status)
    except Exception as e:
        print(f"[investigate_command] failed: {e}")
        await update_status(FRIENDLY_ERROR_MESSAGE)
        await log_error_to_channel(video_link, e, interaction.user)
        return

    chunk_size = 4000
    max_chunks = 4  # case breakdowns can run longer than a normal /ask answer
    chunks = [breakdown[i:i + chunk_size] for i in range(0, len(breakdown), chunk_size)] or [""]
    if len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        chunks[-1] = chunks[-1][:chunk_size - 60] + "\n\n*(Response truncated.)*"

    await update_status("Analysis complete.")

    first_embed = discord.Embed(
        title="Case Breakdown",
        description=chunks[0],
        color=discord.Color.blurple()
    )
    await interaction.followup.send(embed=first_embed)

    for chunk in chunks[1:]:
        follow_embed = discord.Embed(description=chunk, color=discord.Color.blurple())
        await interaction.followup.send(embed=follow_embed)

bot.run(TOKEN)
