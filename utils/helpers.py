import os
import discord

OWNER_ID = int(os.getenv('OWNER_ID', '0'))
DEVELOPER_ID = int(os.getenv('DEVELOPER_ID', '0'))

def is_owner(user_id):
    return user_id == OWNER_ID

def is_developer(user_id):
    return user_id == DEVELOPER_ID or is_owner(user_id)

def create_embed(title, description, color=discord.Color.blue(), fields=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed
