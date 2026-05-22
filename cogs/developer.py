import os
import discord
from discord.ext import commands
from utils.helpers import is_developer, is_owner

class DeveloperCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dev')
    async def dev_check(self, ctx):
        """Check if you're a developer"""
        if is_developer(ctx.author.id):
            await ctx.send(f'✅ {ctx.author.mention}, you are a recognized developer!')
        else:
            await ctx.send('❌ You are not a developer.')

    @commands.command(name='reload')
    async def reload_cog(self, ctx, cog: str):
        """Reload a cog (Developer only)"""
        if not is_developer(ctx.author.id):
            return await ctx.send('❌ Developer only!')
        try:
            await self.bot.reload_extension(f'cogs.{cog}')
            await ctx.send(f'✅ Cog `{cog}` reloaded!')
        except Exception as e:
            await ctx.send(f'❌ Error: {e}')

    @commands.command(name='sync')
    async def sync_commands(self, ctx):
        """Sync slash commands (Owner only)"""
        if not is_owner(ctx.author.id):
            return await ctx.send('❌ Owner only!')
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f'✅ Synced {len(synced)} commands!')
        except Exception as e:
            await ctx.send(f'❌ Error: {e}')

    @commands.command(name='shutdown')
    async def shutdown(self, ctx):
        """Shutdown bot (Owner only)"""
        if not is_owner(ctx.author.id):
            return await ctx.send('❌ Owner only!')
        await ctx.send('👋 Shutting down...')
        await self.bot.close()

    @commands.command(name='setowner')
    async def set_owner(self, ctx):
        """Show owner info"""
        owner_id = int(os.getenv('OWNER_ID', '0'))
        developer_id = int(os.getenv('DEVELOPER_ID', '0'))
        embed = discord.Embed(title='👑 Bot Staff', color=discord.Color.gold())
        if owner_id:
            owner = self.bot.get_user(owner_id)
            embed.add_field(name='Owner', value=f'{owner.mention if owner else "Unknown"} (`{owner_id}`)', inline=False)
        if developer_id:
            dev = self.bot.get_user(developer_id)
            embed.add_field(name='Developer', value=f'{dev.mention if dev else "Unknown"} (`{developer_id}`)', inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print('✅ Developer cog ready!')


async def setup(bot):
    await bot.add_cog(DeveloperCog(bot))
