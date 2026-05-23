import discord
from discord.ext import commands
from datetime import datetime, timezone

# --- زر استعادة القناة (تفاعلي) ---
class RestoreChannelView(discord.ui.View):
    def __init__(self, channel_name, channel_type, category_id):
        super().__init__(timeout=None)
        self.c_name = channel_name
        self.c_type = channel_type
        self.c_cat_id = category_id

    @discord.ui.button(label="استعادة القناة ♻️", style=discord.ButtonStyle.success)
    async def restore_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = guild.get_channel(self.c_cat_id) if self.c_cat_id else None
        
        try:
            if str(self.c_type) == "text":
                await guild.create_text_channel(name=self.c_name, category=category)
            elif str(self.c_type) == "voice":
                await guild.create_voice_channel(name=self.c_name, category=category)
            
            button.disabled = True
            button.label = "تمت الاستعادة ✅"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ تم استعادة قناة `{self.c_name}` بنجاح!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)


class EventsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # دالة إرسال السجلات عبر Webhook (الخلطة السرية للفخامة)
    async def send_webhook_log(self, guild: discord.Guild, embed: discord.Embed, view: discord.ui.View = None):
        g_id = str(guild.id)
        log_chan_id = self.bot.db.get(g_id, {}).get('log_channel')
        if not log_chan_id: return
        
        channel = guild.get_channel(log_chan_id)
        if not channel: return
        
        try:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name="EchoGuard-AI System")
            if not webhook:
                webhook = await channel.create_webhook(name="EchoGuard-AI System")
            
            # صورة المرسل فخمة كأنه ذكاء اصطناعي حقيقي
            avatar_url = "https://i.postimg.cc/SNrRy2JS/chouaibchou13-pindown-io-1779531490.png"
            
            if view:
                await webhook.send(embed=embed, view=view, username="EchoGuard Guardian", avatar_url=avatar_url)
            else:
                await webhook.send(embed=embed, username="EchoGuard Guardian", avatar_url=avatar_url)
        except Exception as e:
            print(f"Webhook Log Error: {e}")

    # 1. نظام الترحيب والرتب التلقائية
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g_id = str(member.guild.id) 
        data = self.bot.db.get(g_id, {})
        
        # --- رتبة تلقائية ---
        auto_role_id = data.get('auto_role')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try: await member.add_roles(role)
                except Exception: pass
        
        # --- الترحيب ---
        welcome_channel_id = data.get('welcome_channel')
        channel = member.guild.get_channel(welcome_channel_id) if welcome_channel_id else None
        
        if channel:
            rules_channel_id = data.get('rules_channel')
            rules_mention = f"<#{rules_channel_id}>" if rules_channel_id else "`قناة القوانين`"
            banner_url = data.get('banner_url') or "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg"
            
            embed = discord.Embed(
                title=f"✨ أهلاً بك في {member.guild.name}! ✨",
                description=(
                    f"> **مرحباً بك يا {member.mention}!**\n"
                    f"> أنت العضو المتميز رقم **{member.guild.member_count}** 🎉\n\n"
                    f"📌 **يرجى مراجعة القوانين هنا:** {rules_mention}"
                ),
                color=discord.Color.from_str("#00f2ff")
            )
            if member.avatar: embed.set_thumbnail(url=member.avatar.url)
            embed.set_image(url=banner_url)
            await channel.send(content=f"👋 حياك الله {member.mention}!", embed=embed)

        # --- سجل دخول العضو (مع تحليل عمر الحساب) ---
        acc_age = (datetime.now(timezone.utc) - member.created_at).days
        warning = "🔴 **تحذير: الحساب جديد جداً!**" if acc_age < 3 else "🟢 الحساب موثوق العمر."
        
        log_embed = discord.Embed(title="📥 دخول عضو جديد", color=discord.Color.green())
        log_embed.add_field(name="العضو:", value=f"{member.mention} ({member.name})", inline=True)
        log_embed.add_field(name="تاريخ إنشاء الحساب:", value=f"قبل {acc_age} يوم\n{warning}", inline=False)
        if member.avatar: log_embed.set_thumbnail(url=member.avatar.url)
        await self.send_webhook_log(member.guild, log_embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        roles_str = " ".join(roles) if roles else "لا يملك رتب"
        
        embed = discord.Embed(title="📤 خروج عضو", color=discord.Color.red())
        embed.add_field(name="العضو:", value=f"{member.mention} ({member.name})", inline=True)
        embed.add_field(name="الرتب التي كان يملكها:", value=roles_str, inline=False)
        await self.send_webhook_log(member.guild, embed)

    # 2. نظام الرد التلقائي
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        
        g_id = str(message.guild.id)
        auto_responses = self.bot.db.get(g_id, {}).get('auto_responses', {})
        msg_content = message.content.strip().lower()
        
        for keyword, response in auto_responses.items():
            if keyword in msg_content:
                await message.channel.send(response)
                break 

    # 3. سجلات الرسائل
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        embed = discord.Embed(title="🗑️ رسالة محذوفة", color=discord.Color.red())
        embed.add_field(name="الكاتب:", value=message.author.mention, inline=True)
        embed.add_field(name="القناة:", value=message.channel.mention, inline=True)
        
        # حفظ محتوى الرسالة
        content = message.content if message.content else "لا يوجد نص (صورة أو ملف)"
        embed.add_field(name="المحتوى (صندوق أسود):", value=f"```\n{content}\n```", inline=False)
        
        if message.attachments:
            embed.add_field(name="مرفقات:", value=f"الرسالة كانت تحتوي على {len(message.attachments)} ملفات/صور.", inline=False)
            
        await self.send_webhook_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content or not before.guild: return
        embed = discord.Embed(title="📝 تعديل رسالة", color=discord.Color.orange())
        embed.add_field(name="الكاتب:", value=before.author.mention, inline=True)
        embed.add_field(name="القناة:", value=f"[الذهاب للرسالة]({after.jump_url})", inline=True)
        embed.add_field(name="القديم:", value=f"```\n{before.content}\n```", inline=False)
        embed.add_field(name="الجديد:", value=f"```\n{after.content}\n```", inline=False)
        await self.send_webhook_log(before.guild, embed)

    # 4. سجلات القنوات والأزرار التفاعلية
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(title="📁 إنشاء قناة", color=discord.Color.green())
        embed.add_field(name="الاسم:", value=channel.name, inline=True)
        embed.add_field(name="النوع:", value=str(channel.type), inline=True)
        await self.send_webhook_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(title="🧨 حذف قناة", color=discord.Color.dark_red())
        embed.add_field(name="القناة المحذوفة:", value=channel.name, inline=True)
        cat_id = channel.category.id if channel.category else None
        
        view = RestoreChannelView(channel.name, channel.type, cat_id)
        await self.send_webhook_log(channel.guild, embed, view=view)

    # 5. التغييرات في الرتب (اللون الأخضر للإضافة والأحمر للسحب)
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles: return
        embed = discord.Embed(title="🏷️ تعديل رتب العضو", color=discord.Color.teal())
        embed.add_field(name="العضو:", value=after.mention, inline=False)
        
        added_roles = [role.mention for role in after.roles if role not in before.roles]
        removed_roles = [role.mention for role in before.roles if role not in after.roles]
        
        if added_roles: embed.add_field(name="الرتب المضافة 🟢", value=" | ".join(added_roles), inline=False)
        if removed_roles: embed.add_field(name="الرتب المسحوبة 🔴", value=" | ".join(removed_roles), inline=False)
        
        await self.send_webhook_log(after.guild, embed)

    # 6. تحديثات الروم الصوتي
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel: return
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=member.name, icon_url=member.avatar.url if member.avatar else None)
        
        if not before.channel and after.channel:
            embed.title = "🔊 دخول صوتي"
            embed.description = f"دخل {member.mention} إلى ➔ **{after.channel.name}**"
        elif before.channel and not after.channel:
            embed.title = "🔇 خروج صوتي"
            embed.description = f"خرج {member.mention} من ➔ **{before.channel.name}**"
        elif before.channel and after.channel:
            embed.title = "🔀 انتقال صوتي"
            embed.description = f"انتقل {member.mention} \nمن: **{before.channel.name}** \nإلى: **{after.channel.name}**"
        
        await self.send_webhook_log(member.guild, embed)

async def setup(bot):
    await bot.add_cog(EventsHandler(bot))
