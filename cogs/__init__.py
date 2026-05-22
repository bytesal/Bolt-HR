from .jobs import JobsCog
from .staff import StaffCog
from .developer import DeveloperCog

async def setup(bot):
    await bot.add_cog(JobsCog(bot))
    await bot.add_cog(StaffCog(bot))
    await bot.add_cog(DeveloperCog(bot))
