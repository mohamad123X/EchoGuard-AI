import discord
from discord.ext import commands

class EventsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. حدث دخول الأعضاء (الترحيب الاحترافي + الرتبة التلقائية)
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g_id = member.guild.id
        data = self.bot.db.get(g_id, {})
        
        # --- تفعيل الرتبة التلقائية (Auto-Role) ---
        auto_role_id = data.get('auto_role')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try: await member.add_roles(role)
                except Exception: pass
        
        # --- تفعيل نظام الترحيب الذكي مع تلافي الأخطاء السابقة ---
        welcome_channel_id = data.get('welcome_channel')
        channel = member.guild.get_channel(welcome_channel_id) if welcome_channel_id else discord.utils.get(member.guild.text_channels, name="welcome")
        
        if not channel: return
        
        rules_channel_id = data.get('rules_channel')
        rules_mention = f"<#{rules_channel_id}>" if rules_channel_id else "`قناة القوانين`"
        server_name = member.guild.name
        banner_url = data.get('banner_url', "https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?q=80&w=1000&auto=format&fit=crop")
        
        embed = discord.Embed(
            title=f"✨ أهلاً بك في {server_name}! ✨",
            description=(
                f"> **مرحباً بك يا {member.mention} في بيتك الجديد!**\n"
                f"> أنت العضو المتميز رقم **{member.guild.member_count}** بالسيرفر 🎉\n\n"
                f"📌 **يرجى مراجعة القوانين والأنظمة هنا:** {rules_mention}\n"
                f"💬 **نتمنى لك قضاء وقت ممتع وتفاعل أسطوري معنا!**"
            ),
            color=discord.Color.from_str("#ff00a0") # نيون وردي جذاب للترحيب
        )
        if member.avatar: embed.set_thumbnail(url=member.avatar.url)
        embed.set_image(url=banner_url)
        embed.set_footer(text=f"Welcome to {server_name}", icon_url=member.guild.icon.url if member.guild.icon else None)
        
        await channel.send(content=f"👋 حياك الله {member.mention}!", embed=embed)


    # 2. حدث الرد التلقائي (Auto-Responder)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        
        g_id = message.guild.id
        auto_responses = self.bot.db.get(g_id, {}).get('auto_responses', {})
        
        msg_content = message.content.strip()
        if msg_content in auto_responses:
            await message.channel.send(auto_responses[msg_content])


    # 3. أحداث السجل والتقارير المفصلة (Log System)
    async def send_log(self, guild: discord.Guild, embed: discord.Embed):
        log_chan_id = self.bot.db.get(guild.id, {}).get('log_channel')
        if log_chan_id:
            channel = guild.get_channel(log_chan_id)
            if channel: await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        embed = discord.Embed(title="🗑️ تم حذف رسالة", color=discord.Color.red())
        embed.add_field(name="الكاتب:", value=message.author.mention, inline=True)
        embed.add_field(name="القناة:", value=message.channel.mention, inline=True)
        embed.add_field(name="محتوى الرسالة:", value=message.content or "صورة/ملف", inline=False)
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content or not before.guild: return
        embed = discord.Embed(title="📝 تم تعديل رسالة", color=discord.Color.orange())
        embed.add_field(name="الكاتب:", value=before.author.mention, inline=True)
        embed.add_field(name="القناة:", value=before.channel.mention, inline=True)
        embed.add_field(name="قبل التعديل:", value=before.content, inline=False)
        embed.add_field(name="بعد التعديل:", value=after.content, inline=False)
        await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel: return
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else None)
        
        if not before.channel and after.channel:
            embed.title = "🔊 دخول قناة صوتية"
            embed.description = f"انضم {member.mention} إلى روم صوتي: **{after.channel.name}**"
        elif before.channel and not after.channel:
            embed.title = "🔇 خروج من قناة صوتية"
            embed.description = f"غادر {member.mention} الروم الصوتي: **{before.channel.name}**"
        elif before.channel and after.channel:
            embed.title = "🔀 انتقال بين القنوات الصوتية"
            embed.description = f"انتقل {member.mention} من **{before.channel.name}** إلى **{after.channel.name}**"
        else: return
        
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles: return
        embed = discord.Embed(title="🏷️ تعديل رتب العضو", color=discord.Color.teal())
        embed.add_field(name="العضو:", value=after.mention, inline=False)
        
        added_roles = [role.mention for role in after.roles if role not in before.roles]
        removed_roles = [role.mention for role in before.roles if role not in after.roles]
        
        if added_roles: embed.add_field(name="الرتب التي تم منحها 🟢:", value=", ".join(added_roles), inline=False)
        if removed_roles: embed.add_field(name="الرتب التي تم سحبها 🔴:", value=", ".join(removed_roles), inline=False)
        
        await self.send_log(after.guild, embed)

async def setup(bot):
    await bot.add_cog(EventsHandler(bot))
