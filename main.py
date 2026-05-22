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
    await bot.change_presence(activity=discord.Game(name=f'{os.getenv("PREFIX", "!")}help'))

# ========== HELP COMMAND ==========
@bot.command(name='help')
async def help_command(ctx):
    """Show all bot commands"""
    prefix = os.getenv('PREFIX', '!')
    
    embed = discord.Embed(
        title='🤖 Bot Help Menu',
        description=f'All commands use prefix `{prefix}`',
        color=discord.Color.blue()
    )
    
    # General Commands (everyone)
    embed.add_field(
        name='📋 General',
        value=f'`{prefix}help` - Show this menu\n'
              f'`{prefix}dev` - Check developer status\n'
              f'`{prefix}setowner` - Show bot owner/dev info',
        inline=False
    )
    
    # Job Application Commands
    embed.add_field(
        name='💼 Job Applications (Admin)',
        value=f'`{prefix}post_jobs` - Post job announcement\n'
              f'`{prefix}addjob <name> <desc>` - Add job\n'
              f'`{prefix}removejob <name>` - Remove job\n'
              f'`{prefix}addq <job> <question>` - Add question\n'
              f'`{prefix}removeq <job> <index>` - Remove question\n'
              f'`{prefix}viewjob <name>` - View job details\n'
              f'`{prefix}applications [job]` - View applications\n'
              f'`{prefix}sethr` - Set HR review channel\n'
              f'`{prefix}setlog` - Set HR log channel\n'
              f'`{prefix}hrlogs [@reviewer]` - View decision logs',
        inline=False
    )
    
    # Staff Ranks Commands
    embed.add_field(
        name='👥 Staff Ranks (Admin)',
        value=f'`{prefix}post_staff` - Post staff ranks panel\n'
              f'`{prefix}addrank <name> <emoji> <desc>` - Add rank\n'
              f'`{prefix}addduty <rank> <duty>` - Add duty\n'
              f'`{prefix}removerank <name>` - Remove rank',
        inline=False
    )
    
    # Developer/Owner Commands
    if is_developer(ctx.author.id) or is_owner(ctx.author.id):
        embed.add_field(
            name='🔧 Developer',
            value=f'`{prefix}reload <cog>` - Reload a cog\n'
                  f'`{prefix}sync` - Sync slash commands (owner)\n'
                  f'`{prefix}shutdown` - Shutdown bot (owner)',
            inline=False
        )
    
    embed.set_footer(text='For more help, contact the bot developer.')
    await ctx.send(embed=embed)

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
