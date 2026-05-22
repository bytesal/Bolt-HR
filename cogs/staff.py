import discord
from discord.ext import commands
from config import db

class StaffSelect(discord.ui.Select):
    def __init__(self, ranks):
        options = []
        for rank in ranks:
            options.append(discord.SelectOption(label=rank['name'], value=rank['name'], description=rank.get('description', '')[:100], emoji=rank.get('emoji', '👤')))
        if not options:
            options.append(discord.SelectOption(label='No ranks configured', value='none'))
        super().__init__(placeholder='Select a staff rank to view duties...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'none':
            await interaction.response.send_message('No ranks configured.', ephemeral=True)
            return
        ranks = await db.get_all_staff_ranks()
        rank = next((r for r in ranks if r['name'] == self.values[0]), None)
        if not rank:
            return
        embed = discord.Embed(title=f'{rank.get("emoji", "👤")} {rank["name"]}', description=rank.get('description', ''), color=discord.Color.purple())
        duties = rank.get('duties', [])
        if duties:
            embed.add_field(name='📋 Responsibilities', value='\n'.join([f'• {d}' for d in duties]), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class StaffView(discord.ui.View):
    def __init__(self, ranks):
        super().__init__(timeout=None)
        self.add_item(StaffSelect(ranks))


class StaffCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='post_staff')
    @commands.has_permissions(administrator=True)
    async def post_staff(self, ctx):
        """Post staff ranks panel"""
        ranks = await db.get_all_staff_ranks()
        if not ranks:
            return await ctx.send('❌ No staff ranks. Use `!addrank` first.')
        embed = discord.Embed(title='👥 Staff Team', description='Select a rank to view responsibilities.', color=discord.Color.purple())
        await ctx.send(embed=embed, view=StaffView(ranks))

    @commands.command(name='addrank')
    @commands.has_permissions(administrator=True)
    async def add_rank(self, ctx, name: str, emoji: str, *, description: str):
        """Add a staff rank. Format: !addrank <name> <emoji> <description>"""
        ranks = await db.get_all_staff_ranks()
        if any(r['name'] == name for r in ranks):
            return await ctx.send(f'❌ Rank `{name}` already exists!')
        await db.add_staff_rank(name, description, emoji, [])
        await ctx.send(f'✅ Rank **{name}** created! Use `!addduty {name} <duty>` to add duties.')

    @commands.command(name='addduty')
    @commands.has_permissions(administrator=True)
    async def add_duty(self, ctx, rank_name: str, *, duty: str):
        """Add a duty to a staff rank"""
        ranks = await db.get_all_staff_ranks()
        rank = next((r for r in ranks if r['name'] == rank_name), None)
        if not rank:
            return await ctx.send(f'❌ Rank `{rank_name}` not found!')
        duties = rank.get('duties', [])
        duties.append(duty)
        await db.staff_ranks.update_one({'name': rank_name}, {'$set': {'duties': duties}})
        await ctx.send(f'✅ Duty added to **{rank_name}**')

    @commands.command(name='removerank')
    @commands.has_permissions(administrator=True)
    async def remove_rank(self, ctx, *, name: str):
        """Remove a staff rank"""
        await db.delete_staff_rank(name)
        await ctx.send(f'✅ Rank **{name}** removed!')


async def setup(bot):
    await bot.add_cog(StaffCog(bot))
