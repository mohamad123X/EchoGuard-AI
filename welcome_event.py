import discord
from discord.ext import commands

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        
        # التحقق مما إذا كان السيرفر قد قام بإعداد نظام الترحيب
        if guild_id not in self.bot.db:
            return
            
        data = self.bot.db[guild_id]
        channel_id = data.get('welcome_channel')
        rules_id = data.get('rules_channel')
        server_name = data.get('server_name', member.guild.name)
        banner_url = data.get('banner_url')
        
        channel = member.guild.get_channel(channel_id)
        if not channel: return # إذا تم حذف القناة

        # إنشاء الـ Embed الراقي بألوان متناسقة مع البنر (أزرق مخضر/نيون)
        embed = discord.Embed(
            title=f"Welcome {member.name} to {server_name}!",
            description=f"You are member **{member.guild.member_count}** 🎉\n"
                        "-------------------------------\n"
                        f"📌 Please read the <#{rules_id}>\n"
                        "💬 Chat & have fun\n"
                        "🚀 Enjoy",
            color=discord.Color.from_str("#00f2ff") 
        )
        
        # صورة المستخدم في أعلى اليمين بشكل دائري (Thumbnail)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
            
        # صورة البنر العريضة في أسفل الترحيب
        embed.set_image(url=banner_url)
        
        # إرسال الرسالة مع عمل Mention للعضو خارج الـ Embed لضمان وصول الإشعار
        await channel.send(content=f"Welcome {member.mention}!", embed=embed)

# لا تنسَ تحميل هذا الكوج في main.py
async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
