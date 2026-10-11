# Mallow — Python Discord Bot

Prefix-only Discord moderation bot using `^`.

## Setup
1. Install Python 3.10+.
2. In this folder run: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`.
4. Put your token in `.env`:
   `DISCORD_TOKEN=YOUR_REAL_TOKEN`
5. Run: `python bot.py`

Enable **Message Content Intent** and **Server Members Intent** in the Discord Developer Portal.

## Commands

General:
- `^help`
- `^ping`
- `^userinfo [@user]`
- `^serverinfo`
- `^warnings @user`
- `^modrole`

Moderation:
- `^ban @user [reason]`
- `^kick @user [reason]`
- `^timeout @user <minutes> [reason]`
- `^untimeout @user`
- `^warn @user [reason]`
- `^clearwarnings @user`
- `^clear <amount>`

**Server owner only:**
- `^assignmodrole @role`
- `^announce <message>`

`^announce` makes Mallow send your message as the bot. The command message is deleted when possible.

The assigned moderator role and warnings are saved in `data.json`.
