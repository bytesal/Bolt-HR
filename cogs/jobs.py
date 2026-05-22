import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from config import db
from bson import ObjectId

class ReviewButtons(discord.ui.View):
    def __init__(self, app_id, job_name):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.job_name = job_name

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green, emoji='✅')
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message('❌ No permission!', ephemeral=True)
            return
        modal = DecisionModal(self.app_id, self.job_name, 'accepted')
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Reject', style=discord.ButtonStyle.red, emoji='❌')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message('❌ No permission!', ephemeral=True)
            return
        modal = DecisionModal(self.app_id, self.job_name, 'rejected')
        await interaction.response.send_modal(modal)

class DecisionModal(discord.ui.Modal, title='Decision Reason'):
    def __init__(self, app_id, job_name, decision):
        super().__init__()
        self.app_id = app_id
        self.job_name = job_name
        self.decision = decision
        self.reason_input = discord.ui.TextInput(
            label=f'Reason for {decision}',
            placeholder='Enter detailed reason...',
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value
        # Update status
        await db.update_application_status(self.app_id, self.decision)
        # Add log
        await db.add_log(self.app_id, interaction.user.id, str(interaction.user), self.decision, reason)
        # Update embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green() if self.decision == 'accepted' else discord.Color.red()
        embed.add_field(name=f'{"✅" if self.decision == "accepted" else "❌"} {self.decision.title()}', 
                       value=f'**By:** {interaction.user.mention}\n**Reason:** {reason}', inline=False)
        await interaction.response.edit_message(embed=embed, view=None)
        # Notify applicant
        app = await db.get_application(self.app_id)
        if app:
            applicant = interaction.guild.get_member(app['user_id'])
            if applicant:
                try:
                    msg = f"🎉 Your application for **{self.job_name}** was **{self.decision}**!\n**Reason:** {reason}" if self.decision == 'accepted' else f"📩 Your application for **{self.job_name}** was **{self.decision}**.\n**Reason:** {reason}"
                    await applicant.send(msg)
                except:
                    pass
        # Send to log channel
        log_channel_id = await db.get_log_channel()
        if log_channel_id:
            log_channel = interaction.guild.get_channel(int(log_channel_id))
            if log_channel:
                log_embed = discord.Embed(title='📋 HR Decision Log', color=discord.Color.blue(), timestamp=discord.utils.utcnow())
                log_embed.add_field(name='Application', value=f'#{self.app_id} - {self.job_name}', inline=False)
                log_embed.add_field(name='Applicant', value=f'<@{app["user_id"]}> ({app["user_name"]})', inline=False)
                log_embed.add_field(name='Decision', value=f'{self.decision.upper()} by {interaction.user.mention}', inline=False)
                log_embed.add_field(name='Reason', value=reason, inline=False)
                await log_channel.send(embed=log_embed)

class JobSelect(discord.ui.Select):
    def __init__(self):
        options = []
        jobs_cursor = None  # Will be set in callback
        super().__init__(placeholder='Select a position to apply for...', min_values=1, max_values=1, options=[discord.SelectOption(label='Loading...', value='loading')])

    async def update_options(self):
        jobs = await db.get_all_jobs()
        options = []
        for job in jobs:
            options.append(discord.SelectOption(label=job['name'], value=job['name'], description=job['description'][:100], emoji='💼'))
        if not options:
            options.append(discord.SelectOption(label='No positions available', value='none'))
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'none':
            await interaction.response.send_message('❌ No positions available.', ephemeral=True)
            return
        job_name = self.values[0]
        job = await db.get_job(job_name)
        if not job:
            await interaction.response.send_message('❌ Job not found!', ephemeral=True)
            return
        # Test DM
        try:
            await interaction.user.send('🔍 Testing DM connection...')
        except discord.Forbidden:
            await interaction.response.send_message('❌ **Cannot send DMs!**\nEnable DMs in Privacy Settings.', ephemeral=True)
            return
        await interaction.response.send_message(f'✅ Check your DMs to apply for **{job_name}**!', ephemeral=True)
        await self.process_application(interaction.user, job)

    async def process_application(self, user, job):
        questions = job.get('questions', [])
        if not questions:
            await user.send('❌ No questions configured.')
            return
        await user.send(f'📝 **Application: {job["name"]}**\n{job["description"]}\n\nAnswer {len(questions)} questions.\nType `cancel` to stop.')
        def check(m): return m.author == user and m.guild is None
        answers = {}
        for i, q in enumerate(questions, 1):
            await user.send(f'**Q{i}/{len(questions)}:** {q}')
            try:
                msg = await user.client.wait_for('message', timeout=600.0, check=check)
                if msg.content.lower() == 'cancel':
                    await user.send('❌ Cancelled.')
                    return
                answers[q] = msg.content
            except asyncio.TimeoutError:
                await user.send('⏰ Timed out.')
                return
        await user.send('✅ **Application submitted!**')
        app_id = await db.add_application(user.id, str(user), job['name'], answers)
        hr_channel_id = await db.get_hr_channel()
        if hr_channel_id:
            channel = user.mutual_guilds[0].get_channel(int(hr_channel_id)) if user.mutual_guilds else None
            if not channel and hasattr(user, 'guild'):
                channel = user.guild.get_channel(int(hr_channel_id))
            if channel:
                embed = discord.Embed(title=f'📩 Application - {job["name"]}', color=discord.Color.gold(), timestamp=discord.utils.utcnow())
                embed.set_author(name=str(user), icon_url=user.avatar.url if user.avatar else None)
                embed.add_field(name='👤 Applicant', value=f'{user.mention}\nID: `{user.id}`', inline=False)
                for q, a in answers.items():
                    embed.add_field(name=f'Q: {q[:256]}', value=a[:1024] if len(a) <= 1024 else a[:1021]+'...', inline=False)
                await channel.send(embed=embed, view=ReviewButtons(str(app_id), job['name']))

class JobView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.job_select = JobSelect()
        self.add_item(self.job_select)

    async def update_select(self):
        await self.job_select.update_options()


class JobsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='post_jobs')
    @commands.has_permissions(administrator=True)
    async def post_jobs(self, ctx):
        """Post job announcement with dropdown"""
        jobs = await db.get_all_jobs()
        if not jobs:
            return await ctx.send('❌ No jobs found. Use `!addjob` first.')
        embed = discord.Embed(title='📋 We\'re Hiring!', description='Select a position from the dropdown to apply.', color=discord.Color.blue())
        embed.add_field(name='Available Positions:', value='\n'.join([f'• **{j["name"]}** - {j["description"][:100]}' for j in jobs]), inline=False)
        view = JobView()
        await view.update_select()
        await ctx.send(embed=embed, view=view)

    @commands.command(name='addjob')
    @commands.has_permissions(administrator=True)
    async def add_job(self, ctx, name: str, *, description: str):
        """Add a new job position"""
        existing = await db.get_job(name)
        if existing:
            return await ctx.send(f'❌ Job `{name}` already exists!')
        await db.add_job(name, description)
        await ctx.send(f'✅ Job **{name}** created!')

    @commands.command(name='removejob')
    @commands.has_permissions(administrator=True)
    async def remove_job(self, ctx, *, name: str):
        """Remove a job"""
        job = await db.get_job(name)
        if not job:
            return await ctx.send(f'❌ Job `{name}` not found!')
        await db.delete_job(name)
        await ctx.send(f'✅ Job **{name}** deleted!')

    @commands.command(name='addq')
    @commands.has_permissions(administrator=True)
    async def add_question(self, ctx, job_name: str, *, question: str):
        """Add question to a job"""
        job = await db.get_job(job_name)
        if not job:
            return await ctx.send(f'❌ Job `{job_name}` not found!')
        await db.add_question(job_name, question)
        await ctx.send(f'✅ Question added to **{job_name}**')

    @commands.command(name='removeq')
    @commands.has_permissions(administrator=True)
    async def remove_question(self, ctx, job_name: str, index: int):
        """Remove question by index (1-based)"""
        job = await db.get_job(job_name)
        if not job:
            return await ctx.send(f'❌ Job `{job_name}` not found!')
        if index < 1 or index > len(job.get('questions', [])):
            return await ctx.send(f'❌ Invalid index! (1-{len(job.get("questions", []))})')
        await db.remove_question(job_name, index - 1)
        await ctx.send(f'✅ Question {index} removed from **{job_name}**')

    @commands.command(name='viewjob')
    @commands.has_permissions(administrator=True)
    async def view_job(self, ctx, *, name: str):
        """View job details"""
        job = await db.get_job(name)
        if not job:
            return await ctx.send(f'❌ Job `{name}` not found!')
        embed = discord.Embed(title=f'💼 {job["name"]}', description=job['description'], color=discord.Color.blue())
        qs = '\n'.join([f'{i+1}. {q}' for i, q in enumerate(job.get('questions', []))]) or 'None'
        embed.add_field(name='Questions', value=qs, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='applications')
    @commands.has_permissions(manage_messages=True)
    async def view_apps(self, ctx, job_name: str = None):
        """View applications, optionally filter by job"""
        apps = await db.get_all_applications(job_name)
        if not apps:
            return await ctx.send('❌ No applications found.')
        embed = discord.Embed(title=f'📩 Applications ({len(apps)})', color=discord.Color.blue())
        for i, app in enumerate(apps[:10]):
            embed.add_field(name=f'{i+1}. {app["user_name"]} ({app["job_name"]})', value=f'Status: **{app["status"]}** | {app["timestamp"].strftime("%Y-%m-%d %H:%M") if hasattr(app["timestamp"], "strftime") else "N/A"}', inline=False)
        if len(apps) > 10:
            embed.set_footer(text=f'Showing 10 of {len(apps)}')
        await ctx.send(embed=embed)

    @commands.command(name='sethr')
    @commands.has_permissions(administrator=True)
    async def set_hr_channel(self, ctx):
        """Set current channel as HR review channel"""
        await db.set_hr_channel(str(ctx.channel.id))
        await ctx.send(f'✅ HR review channel set to {ctx.channel.mention}')

    @commands.command(name='setlog')
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx):
        """Set current channel as HR logs channel"""
        await db.set_log_channel(str(ctx.channel.id))
        await ctx.send(f'✅ HR log channel set to {ctx.channel.mention}')

    @commands.command(name='hrlogs')
    @commands.has_permissions(manage_messages=True)
    async def hr_logs(self, ctx, reviewer: discord.Member = None):
        """View HR decision logs, optionally filter by reviewer"""
        if reviewer:
            logs = await db.get_reviewer_logs(reviewer.id)
        else:
            logs = await db.get_all_logs()
        if not logs:
            return await ctx.send('❌ No logs found.')
        embed = discord.Embed(title='📋 HR Decision Logs', color=discord.Color.purple())
        for i, log in enumerate(logs[:10]):
            embed.add_field(name=f'{i+1}. App #{log.get("application_id", "N/A")}', value=f'**Decision:** {log["decision"].upper()}\n**By:** {log["reviewer_name"]}\n**Reason:** {log["reason"][:100]}', inline=False)
        if len(logs) > 10:
            embed.set_footer(text=f'Showing 10 of {len(logs)}')
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print('✅ Jobs cog ready!')


async def setup(bot):
    await bot.add_cog(JobsCog(bot))
