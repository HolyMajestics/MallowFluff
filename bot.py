import json
import os
from datetime import timedelta
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

PREFIX = "^"
DATA_FILE = Path("data.json")

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Create a .env file and add your bot token.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True
client = discord.Client(intents=intents)


bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    activity=discord.Game(name="^help | Mallow 🍡"),
)




def load_data():
    if not DATA_FILE.exists():
        return {"guilds": {}}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"guilds": {}}

data = load_data()
data.setdefault("guilds", {})

def save_data():
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def guild_data(guild):
    gd = data["guilds"].setdefault(str(guild.id), {"mod_role_id": None, "warnings": {}})
    gd.setdefault("mod_role_id", None)
    gd.setdefault("warnings", {})
    return gd

def get_mod_role(guild):
    role_id = guild_data(guild)["mod_role_id"]
    return guild.get_role(int(role_id)) if role_id else None

def is_owner(ctx):
    return ctx.guild is not None and ctx.author.id == ctx.guild.owner_id

def is_moderator(member):
    if member.id == member.guild.owner_id or member.guild_permissions.administrator:
        return True
    role = get_mod_role(member.guild)
    return role is not None and role in member.roles

async def require_owner(ctx):
    if ctx.guild is None:
        await ctx.send("❌🐾 Eep! Mallow can only do that inside a server, nya!")
        return False
    if not is_owner(ctx):
        await ctx.send("❌🐾 Eep! Only the server owner can use this one, fluff-friend!")
        return False
    return True

async def require_mod(ctx):
    if ctx.guild is None:
        await ctx.send("❌🐾 Eep! Mallow can only do that inside a server, nya!")
        return False
    if not isinstance(ctx.author, discord.Member) or not is_moderator(ctx.author):
        await ctx.send("❌🐾 Eep! You need moderator permissions for that, fluff-friend!")
        return False
    return True

def target_is_higher(actor, target):
    return target.id == actor.guild.owner_id or target.top_role >= actor.top_role

def bot_can_act(target):
    me = target.guild.me
    return me is not None and target.top_role < me.top_role

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Mallow is online and feeling fluffy! 🐾🍡")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🍡🐾 Mallow Command Book", description="Hewwo! Here are my fluffy little commands! Prefix: `^`", color=discord.Color.blurple())
    embed.add_field(name="🐾 General", value="`^help`\n`^ping`\n`^userinfo [@user]`\n`^serverinfo`\n`^warnings @user`\n`^modrole`", inline=False)
    embed.add_field(name="🛡️🐾 Moderation", value="`^ban @user [reason]`\n`^kick @user [reason]`\n`^timeout @user <minutes> [reason]`\n`^untimeout @user`\n`^warn @user [reason]`\n`^clearwarnings @user`\n`^clear <amount>`", inline=False)
    embed.add_field(name="👑🐾 Owner only", value="`^assignmodrole @role`\n`^announce <message>`", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓🐾 Pawng! Mallow is wide awake and ready to help! `{round(bot.latency * 1000)}ms`")

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if ctx.guild is None:
        return await ctx.send("❌🐾 Eep! Mallow can only do that inside a server, nya!")
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member}", color=discord.Color.blurple())
    embed.add_field(name="User ID", value=str(member.id), inline=False)
    embed.add_field(name="Account created", value=discord.utils.format_dt(member.created_at, "F"), inline=False)
    if member.joined_at:
        embed.add_field(name="Joined server", value=discord.utils.format_dt(member.joined_at, "F"), inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    if ctx.guild is None:
        return await ctx.send("❌🐾 Eep! Mallow can only do that inside a server, nya!")
    g = ctx.guild
    embed = discord.Embed(title=f"🏠 {g.name}", color=discord.Color.blurple())
    embed.add_field(name="Owner", value=f"<@{g.owner_id}>", inline=True)
    embed.add_field(name="Members", value=str(g.member_count), inline=True)
    embed.add_field(name="Channels", value=str(len(g.channels)), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if not await require_mod(ctx): return
    if member.id == ctx.author.id or target_is_higher(ctx.author, member):
        return await ctx.send("❌🐾 Eep! You cannot ban yourself or someone with an equal or higher role.")
    if not bot_can_act(member):
        return await ctx.send("❌ Mallow's role is not high enough to ban that member.")
    try:
        await member.ban(reason=f"{ctx.author}: {reason}")
        await ctx.send(f"🔨🐾 Bonk! **{member}**. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌🐾 Eep! Discord denied the ban. Check Mallow's permissions and role position.")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if not await require_mod(ctx): return
    if member.id == ctx.author.id or target_is_higher(ctx.author, member):
        return await ctx.send("❌🐾 Eep! You cannot kick yourself or someone with an equal or higher role.")
    if not bot_can_act(member):
        return await ctx.send("❌ Mallow's role is not high enough to kick that member.")
    try:
        await member.kick(reason=f"{ctx.author}: {reason}")
        await ctx.send(f"👢🐾 Whoopsie! **{member}**. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌🐾 Eep! Discord denied the kick. Check Mallow's permissions and role position.")

@bot.command()
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    if not await require_mod(ctx): return
    if not 1 <= minutes <= 40320:
        return await ctx.send("❌🐾 Timeout zoomies must be between 1 and 40320 minutes!")
    if member.id == ctx.author.id or target_is_higher(ctx.author, member):
        return await ctx.send("❌🐾 Eep! You cannot timeout yourself or someone with an equal or higher role.")
    if not bot_can_act(member):
        return await ctx.send("❌ Mallow's role is not high enough to timeout that member.")
    try:
        await member.timeout(timedelta(minutes=minutes), reason=f"{ctx.author}: {reason}")
        await ctx.send(f"⏳🐾 Shhh... **{member}** for {minutes} minute(s). Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌🐾 Eep! Discord denied the timeout. Check Mallow's permissions.")

@bot.command()
async def untimeout(ctx, member: discord.Member):
    if not await require_mod(ctx): return
    if target_is_higher(ctx.author, member):
        return await ctx.send("❌ You cannot modify someone with an equal/higher role.")
    try:
        await member.timeout(None, reason=f"Timeout removed by {ctx.author}")
        await ctx.send(f"✨🐾 Yay! **{member}**.")
    except discord.Forbidden:
        await ctx.send("❌🐾 Eep! Discord wouldn't let me remove that timeout.")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    if not await require_mod(ctx): return
    if member.id == ctx.author.id or target_is_higher(ctx.author, member):
        return await ctx.send("❌🐾 Eep! You cannot warn yourself or someone with an equal or higher role.")
    gd = guild_data(ctx.guild)
    warnings = gd["warnings"].setdefault(str(member.id), [])
    warnings.append({"reason": reason, "moderator_id": ctx.author.id})
    save_data()
    await ctx.send(f"⚠️🐾 Uh-oh! **{member}**. They now have **{len(warnings)}** warning(s). Reason: {reason}")

@bot.command()
async def warnings(ctx, member: discord.Member):
    if ctx.guild is None:
        return await ctx.send("❌🐾 Eep! Mallow can only do that inside a server, nya!")
    entries = guild_data(ctx.guild)["warnings"].get(str(member.id), [])
    if not entries:
        return await ctx.send(f"✅ **{member}** has no warnings.")
    lines = [f"**{i}.** {x['reason']} — <@{x['moderator_id']}>" for i, x in enumerate(entries, 1)]
    await ctx.send(embed=discord.Embed(title=f"⚠️ Warnings for {member}", description="\n".join(lines), color=discord.Color.orange()))

@bot.command()
async def clearwarnings(ctx, member: discord.Member):
    if not await require_mod(ctx): return
    guild_data(ctx.guild)["warnings"].pop(str(member.id), None)
    save_data()
    await ctx.send(f"🧹🐾 All warnings for **{member}**.")

@bot.command()
async def clear(ctx, amount: int):
    if not await require_mod(ctx): return
    if not 1 <= amount <= 100:
        return await ctx.send("❌🐾 Please choose an amount between 1 and 100, fluff-friend!")
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹🐾 Sweep-sweep! Mallow deleted **{max(0, len(deleted)-1)}** message(s).", delete_after=3)
    except discord.Forbidden:
        await ctx.send("❌🐾 Eep! Mallow needs the **Manage Messages** permission to do that.")

@bot.command()
async def assignmodrole(ctx, role: discord.Role):
    # OWNER ONLY: checks the actual Discord server owner ID.
    if not await require_owner(ctx): return
    if role.is_default():
        return await ctx.send("❌🐾 Mallow can't make @everyone the moderator role, fluff-friend!")
    if ctx.guild.me and role >= ctx.guild.me.top_role:
        return await ctx.send("❌🐾 Mallow's role needs to sit higher than the moderator role, nya!")
    guild_data(ctx.guild)["mod_role_id"] = role.id
    save_data()
    await ctx.send(f"🛡️🐾 Yay! **{role.name}**.")

@bot.command()
async def modrole(ctx):
    if ctx.guild is None: return
    role = get_mod_role(ctx.guild)
    await ctx.send(f"🛡️ Current moderator role: **{role.name}**" if role else "ℹ️ No moderator role has been assigned yet.")

@bot.command()
async def announce(ctx, *, message):
    # OWNER ONLY: checks the actual Discord server owner ID.
    if not await require_owner(ctx): return
    if not message.strip():
        return await ctx.send("❌🐾 Eep! Give Mallow a message to announce!")
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass
    await ctx.send(f" {message}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send(f"❌🐾 Eep! Something is missing or I couldn't understand that. Try `{PREFIX}help`.")
        return
    if isinstance(error, commands.CommandInvokeError):
        print(f"Command error: {error.original}")
        await ctx.send("❌🐾 Eep! My fluff got tangled while running that command. Please try again!")
        return
    print(f"Unhandled command error: {error}")
    
    
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle)
    print(f'{client.user} has connected to Discord!')
    


bot.run(TOKEN)

