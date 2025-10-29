# --- audioop bypass for Python 3.13 environments like Render ---
import sys, types
sys.modules['audioop'] = types.ModuleType('audioop')
# ---------------------------------------------------------------
# --- keep-alive server for Render ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Zander Verification Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()
# --- end of keep-alive server ---

import discord
from discord.ext import commands, tasks
import warnings
warnings.filterwarnings("ignore", message="audioop")
from discord import app_commands, Embed, ButtonStyle
from discord.ui import View, Button
import os

# --- CONFIGURATION ---
TOKEN = os.getenv("TOKEN")  # token will be set later in Render
GUILD_ID = 1428650568250953758  # replace with your server ID
VERIFICATION_CHANNEL_ID = 1428709658415337605  # replace with your #verification channel ID
REVIEW_CHANNEL_ID = 1430539644134494229  # replace with your private review channel ID
VERIFIED_ROLE_NAME = "Verified members"  # name of the role to assign after verification
# ----------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

class VerifyButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Verify", style=ButtonStyle.green, custom_id="verify_button"))

class ReviewButtons(View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member

        approve_button = Button(label="Approve ✅", style=ButtonStyle.success)
        reject_button = Button(label="Reject ❌", style=ButtonStyle.danger)

        approve_button.callback = self.approve
        reject_button.callback = self.reject

        self.add_item(approve_button)
        self.add_item(reject_button)

    async def approve(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="Verified members")
        if role:
            await self.member.add_roles(role)
            await interaction.response.send_message(f"✅ {self.member.mention} is now verified!", ephemeral=False)
            try:
                await self.member.send("🎉 You’ve been verified! Welcome to the community!")
            except:
                pass
        else:
            await interaction.response.send_message("⚠️ Verified role not found.", ephemeral=True)

    async def reject(self, interaction: discord.Interaction):
        try:
            await self.member.send("❌ Your verification was rejected. Please try again in #verification.")
            await interaction.response.send_message(f"❌ {self.member.mention} has been rejected.", ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Could not DM the user.", ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    refresh_verification_message.start()

@tasks.loop(hours=24)
async def refresh_verification_message():
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(VERIFICATION_CHANNEL_ID)
        if channel:
            async for msg in channel.history(limit=10):
                if msg.author == bot.user:
                    await msg.delete()
            embed = Embed(
                title="🪪 Beaulievers Verification",
                description=(
                    "Click the **Verify** button below to start the process in DM.\n\n"
                    "📸 Make sure to:\n"
                    "- Send a photo with 🫰🏻 pose while holding a paper with your name and birthdate (no need to show your face)\n"
                    "- Send your Facebook **profile link**\n"
                    "- Send a **screenshot** showing you:\n"
                    
                    "  1️⃣ Followed my **Facebook profile** → [Click here](https://www.facebook.com/share/16XELgaE47/)\n"
                    "  2️⃣ Followed my **Facebook page** → [Click here](https://www.facebook.com/share/175CgS9dWS/)\n"
                    "  3️⃣ Joined my **Facebook group** → [Click here](https://www.facebook.com/groups/800333518927857/)\n\n"
                    "Once complete, moderators will manually review your submission."
                ),
                color=0x57F287
            )
            await channel.send(embed=embed, view=VerifyButton())
            print("♻️ Verification message refreshed.")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data.get("custom_id") == "verify_button":
        await interaction.response.send_message(
            "Check your DM to continue verification 💌",
            ephemeral=True
        )
        try:
            await interaction.user.send(
                "👋 Ayo! Let’s start your verification.\n\n"
                "Please send the following here:\n"
                "1️⃣ A photo of you doing a 🫰🏻 pose while holding a paper with your name and birthdate (no need to show your face)\n"
                "2️⃣ Your Facebook profile link\n"
                "3️⃣ Screenshot showing you:\n"
                "   - Followed the Facebook profile\n"
                "   - Followed the Facebook page\n"
                "   - Joined the Facebook group"
            )
        except discord.Forbidden:
            await interaction.followup.send("⚠️ Please enable your DMs to continue.", ephemeral=True)
# --- Buttons for moderators in the review channel ---
class ReviewButtons(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member  # the person being reviewed

    @discord.ui.button(label="Approve ✅", style=discord.ButtonStyle.green)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        if role:
            await self.member.add_roles(role)
            await interaction.response.send_message(f"✅ {self.member.mention} has been verified!", ephemeral=False)
            try:
                await self.member.send("🎉 Yey! You’ve been verified! You now have full access to Zander Beaulievers server.")
            except discord.Forbidden:
                pass
        else:
            await interaction.response.send_message("⚠️ Verified role not found.", ephemeral=True)

    @discord.ui.button(label="Reject ❌", style=discord.ButtonStyle.red)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.member.send("❌ Your verification was rejected. Pasaway! Please try again following all instructions carefully.")
            await interaction.response.send_message(f"❌ {self.member.mention} has been rejected and notified.", ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("⚠️ Could not DM the user.", ephemeral=True)

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        review_channel = bot.get_channel(REVIEW_CHANNEL_ID)
        if review_channel:
            guild = bot.get_guild(GUILD_ID)
            member = guild.get_member(message.author.id)  # ✅ convert User → Member

            # If the user isn’t in the server, stop the process
            if not member:
                await message.channel.send("⚠️ You need to be in the server to complete verification.")
                return

            files = [await a.to_file() for a in message.attachments]
            await review_channel.send(
                f"📩 **New verification from:** {member.mention}\n"
                f"🆔 ID: `{member.id}`",
                files=files,
                view=ReviewButtons(member)  # ✅ now passes a Member, not a User
            )

            if message.content:
                await review_channel.send(f"📝 **Message:** {message.content}")

            await message.channel.send("✅ Submission sent! Please wait while moderators verify you.")
        else:
            await message.channel.send("⚠️ Something went wrong. Please try again later.")

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def approve(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=VERIFIED_ROLE_NAME)
    if role:
        await member.add_roles(role)
        await ctx.send(f"✅ {member.mention} is now verified!")
    else:
        await ctx.send("⚠️ Verified role not found.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def reject(ctx, member: discord.Member):
    try:
        await member.send("❌ Please complete the process to get verified. Go to #verification channel again to start.")
        await ctx.send(f"❌ {member.mention} has been rejected and notified.")
    except discord.Forbidden:
        await ctx.send("⚠️ Could not DM the user.")

import os
bot.run(os.getenv("TOKEN"))

