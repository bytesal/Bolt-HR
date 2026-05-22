import os
import discord
from discord.ext import commands
from utils.helpers import is_owner, is_developer

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=os.getenv('PREFIX', '!'), intents=intents, help_command=None)

# Load cogs
async def load_cogs():
    for cog in ['cogs.jobs', 'cogs.staff', 'cogs.developer']:
        try:
            await bot.load_extension(cog)
            print(f'✅ Loaded: {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await load_cogs()
    await bot.change_presence(activity=discord.Game(name=f'{os.getenv("PREFIX", "!")}post_jobs | {os.getenv("PREFIX", "!")}post_staff'))

# Global error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send('❌ You don\'t have permission!')
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f'❌ Missing argument: `{error.param.name}`')
    print(f'Error: {error}')
    await ctx.send(f'❌ An error occurred: {error}')

# Run bot
if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')
    if not token:
        print('❌ BOT_TOKEN not set!')
        exit(1)
    bot.run(token)
