import discord
from discord.ext import commands

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        
        # نظام احتياطي (Fallback) للتجربة في حال لم يتم إعداد قاعدة البيانات بعد
        data = self.bot.db.get(guild_id, {})
        
        # إذا لم يتم تعيين قناة، سيبحث عن قناة اسمها "welcome" كملاذ أخير
        channel_id = data.get('welcome_channel')
        channel = member.guild.get_channel(channel_id) if channel_id else discord.utils.get(member.guild.text_channels, name="welcome")
        
        if not channel: 
            return 

        rules_id = data.get('rules_channel', channel.id) # افتراضي إذا لم يحدد
        server_name = data.get('server_name', member.guild.name)
        
        # بنر افتراضي أنيق إذا لم يتم تحديد بنر
        banner_url = data.get('banner_url', "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg") 
        
        embed = discord.Embed(
            title=f"✨ مرحباً بك في {server_name}! ✨",
            description=(
                f"> **أهلاً بك يا {member.mention} بيننا!**\n"
                f"> أنت العضو رقم **{member.guild.member_count}** 🎉\n\n"
                f"📌 **يرجى قراءة القوانين في:** <#{rules_id}>\n"
                f"💬 **شاركنا وتفاعل معنا!**\n"
            ),
            color=discord.Color.from_str("#00f2ff") 
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        embed.set_image(url=banner_url)
        embed.set_footer(text=f"Welcome to {server_name}", icon_url=member.guild.icon.url if member.guild.icon else None)
        
        await channel.send(content=f"👋 مرحباً {member.mention}!", embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
