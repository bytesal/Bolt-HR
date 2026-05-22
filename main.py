import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# ========== Bot Setup ==========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=os.getenv('PREFIX', '!'),
    intents=intents,
    help_command=None
)

# ========== Helper Functions ==========
OWNER_ID = int(os.getenv('OWNER_ID', '0'))
DEVELOPER_ID = int(os.getenv('DEVELOPER_ID', '0'))

def is_owner(user_id):
    return user_id == OWNER_ID

def is_developer(user_id):
    return user_id == DEVELOPER_ID or is_owner(user_id)

# ========== Load Cogs ==========
async def load_cogs():
    cogs = ['cogs.jobs', 'cogs.staff', 'cogs.developer']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'✅ Loaded: {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')

# ========== Events ==========
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await load_cogs()
    await bot.change_presence(
        activity=discord.Game(name=f'{os.getenv("PREFIX", "!")}help')
    )

# ========== Help Command ==========
@bot.command(name='help')
async def help_command(ctx):
    prefix = os.getenv('PREFIX', '!')
    embed = discord.Embed(
        title='🤖 Bot Help Menu',
        description=f'All commands use prefix `{prefix}`',
        color=discord.Color.blue()
    )

    embed.add_field(
        name='📋 General',
        value=f'`{prefix}help` - Show this menu\n'
              f'`{prefix}dev` - Check developer status\n'
              f'`{prefix}setowner` - Show bot owner/dev info',
        inline=False
    )

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

    embed.add_field(
        name='👥 Staff Ranks (Admin)',
        value=f'`{prefix}post_staff` - Post staff ranks panel\n'
              f'`{prefix}addrank <name> <emoji> <desc>` - Add rank\n'
              f'`{prefix}addduty <rank> <duty>` - Add duty\n'
              f'`{prefix}removerank <name>` - Remove rank',
        inline=False
    )

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

# ========== Global Error Handler ==========
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send("❌ You don't have permission!")
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f"❌ Missing argument: `{error.param.name}`")
    print(f'Error: {error}')
    await ctx.send(f'❌ An error occurred: {error}')

# ========== Flask HTTP Server for Render Port Binding ==========
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is alive!'

def run_http():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== Run Bot & HTTP Server ==========
if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')
    if not token:
        print('❌ BOT_TOKEN not set!')
        exit(1)

    # Start HTTP server in a background thread
    threading.Thread(target=run_http, daemon=True).start()

    # Start the Discord bot
    bot.run(token)
