import discord
from discord.ext import commands
from datetime import datetime, timezone

# ================== واجهات الأزرار التفاعلية الذكية ==================

class UndoRoleChangeView(discord.ui.View):
    def __init__(self, member_id, added_roles, removed_roles):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.added = added_roles
        self.removed = removed_roles

    @discord.ui.button(label="إلغاء التعديل والتراجع ↩️", style=discord.ButtonStyle.danger)
    async def undo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(self.member_id)
        if not member: 
            return await interaction.response.send_message("❌ العضو غادر السيرفر!", ephemeral=True)
        
        # إزالة ما تم إضافته وإضافة ما تم إزالته (عكس العملية)
        try:
            if self.added: 
                await member.remove_roles(*[interaction.guild.get_role(r) for r in self.added if interaction.guild.get_role(r)])
            if self.removed: 
                await member.add_roles(*[interaction.guild.get_role(r) for r in self.removed if interaction.guild.get_role(r)])
            button.label = "تم التراجع ✅"
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ تم استرجاع رتب {member.mention} السابقة.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ لا أمتلك صلاحية كافية لتعديل الرتب.", ephemeral=True)


class UserProfileView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="ملف السلوك الرقمي 📋", style=discord.ButtonStyle.primary)
    async def profile_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        acc_age = (datetime.now(timezone.utc) - self.user.created_at).days
        embed = discord.Embed(title=f"الملف السلوكي | {self.user.name}", color=discord.Color.dark_theme())
        embed.add_field(name="الآيدي:", value=self.user.id, inline=False)
        embed.add_field(name="عمر الحساب:", value=f"{acc_age} يوم", inline=True)
        embed.add_field(name="ملاحظة النظام:", value="🔴 حساب جديد/خطر" if acc_age < 14 else "🟢 حساب آمن", inline=True)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


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


# ================== النظام الرئيسي (Events Handler) ==================

class EventsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            avatar_url = "https://i.postimg.cc/SNrRy2JS/chouaibchou13-pindown-io-1779531490.png"
            
            if view: 
                await webhook.send(embed=embed, view=view, username="EchoGuard Guardian", avatar_url=avatar_url)
            else: 
                await webhook.send(embed=embed, username="EchoGuard Guardian", avatar_url=avatar_url)
        except: 
            pass

    # ---------------- 1. نظام الرد التلقائي الذكي ----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        
        g_id = str(message.guild.id)
        auto_responses = self.bot.db.get(g_id, {}).get('auto_responses', {})
        
        if not auto_responses: return

        msg_content = message.content.strip().lower()
        
        for keyword, response in auto_responses.items():
            if keyword in msg_content:
                await message.channel.send(response)
                break

    # ---------------- 2. سجلات الأعضاء والترحيب والتحقق ----------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g_id = str(member.guild.id) 
        data = self.bot.db.get(g_id, {})
        
        # الرتبة التلقائية
        auto_role_id = data.get('auto_role')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try: 
                    await member.add_roles(role)
                except Exception: 
                    pass
                
        # نظام الترحيب المطور المتطابق مع الصورة تماماً
        welcome_channel_id = data.get('welcome_channel')
        channel = member.guild.get_channel(welcome_channel_id)
        if channel:
            banner_url = data.get('banner_url') or "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg"
            
            # تنسيق النص والأسطر بدقة هندسية متطابقة مع الصورة
            desc = (
                f"**Welcome** {member.mention} **to {member.guild.name}!**\n"
                f"You are member **{member.guild.member_count}**🎉\n"
                "------------------------------------------------\n"
                "📌 Please read the `#rules`\n"
                "💬 Chat & have fun\n"
                "🚀 Enjoy"
            )

            embed = discord.Embed(
                description=desc, 
                color=discord.Color.from_str("#1a3d36"),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_image(url=banner_url)
            
            # إظهار أيقونة وصورة العضو الجديد في الزاوية العلوية اليمنى بشكل صحيح
            if member.display_avatar:
                embed.set_thumbnail(url=member.display_avatar.url)
            
            try: 
                await channel.send(embed=embed)
            except Exception: 
                pass

        # سجل الدخول وكشف الحسابات الوهمية لإدارة السيرفر
        acc_age = (datetime.now(timezone.utc) - member.created_at).days
        embed_log = discord.Embed(title="📥 دخول عضو", color=discord.Color.green())
        embed_log.add_field(name="العضو:", value=f"{member.mention} ({member.name})")
        embed_log.add_field(name="حالة الحساب:", value="🔴 **حساب جديد (وهمي؟)**" if acc_age < 7 else f"🟢 آمن (منذ {acc_age} يوم)")
        await self.send_webhook_log(member.guild, embed_log, view=UserProfileView(member))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(title="📤 خروج عضو", color=discord.Color.red())
        embed.add_field(name="العضو:", value=f"{member.mention} ({member.name})")
        
        action = "خرج طوعاً من السيرفر🚶"
        if member.guild.me.guild_permissions.view_audit_log:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    action = f"تم طرده (Kick) 🥾 بواسطة {entry.user.mention}\nالسبب: {entry.reason or 'بدون سبب'}"
                    break
                    
        embed.add_field(name="سبب الخروج:", value=action, inline=False)
        await self.send_webhook_log(member.guild, embed, view=UserProfileView(member))

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        embed = discord.Embed(title="🔨 تم حظر عضو (Ban)", color=discord.Color.dark_red())
        embed.add_field(name="العضو:", value=f"{user.mention} ({user.name})")
        await self.send_webhook_log(guild, embed, view=UserProfileView(user))

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = discord.Embed(title="🕊️ تم فك الحظر (Unban)", color=discord.Color.green())
        embed.add_field(name="العضو:", value=f"{user.mention} ({user.name})")
        await self.send_webhook_log(guild, embed, view=UserProfileView(user))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick != after.nick:
            embed = discord.Embed(title="🏷️ تغيير اللقب (Nickname)", color=discord.Color.dark_gray())
            embed.add_field(name="العضو:", value=after.mention)
            embed.add_field(name="اللقب القديم:", value=before.nick or before.name)
            embed.add_field(name="اللقب الجديد:", value=after.nick or after.name)
            await self.send_webhook_log(after.guild, embed)

        if not before.is_timed_out() and after.is_timed_out():
            embed = discord.Embed(title="🤐 تم إسكات عضو (Timeout)", color=discord.Color.orange())
            embed.add_field(name="العضو:", value=after.mention)
            embed.add_field(name="ينتهي في:", value=f"<t:{int(after.timed_out_until.timestamp())}:R>")
            await self.send_webhook_log(after.guild, embed)

        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            
            embed = discord.Embed(title="🎭 تعديل رتب العضو", color=discord.Color.teal())
            embed.add_field(name="العضو:", value=after.mention, inline=False)
            if added: embed.add_field(name="🟢 الرتب المضافة:", value=" | ".join([r.mention for r in added]), inline=False)
            if removed: embed.add_field(name="🔴 الرتب المسحوبة:", value=" | ".join([r.mention for r in removed]), inline=False)
            
            view = UndoRoleChangeView(after.id, [r.id for r in added], [r.id for r in removed])
            await self.send_webhook_log(after.guild, embed, view=view)

    # ---------------- 3. سجلات الرسائل والتنبيهات الذكية ----------------

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        
        embed = discord.Embed(title="🗑️ رسالة محذوفة", color=discord.Color.red())
        embed.add_field(name="الكاتب:", value=message.author.mention, inline=True)
        embed.add_field(name="القناة:", value=message.channel.mention, inline=True)
        
        deleter = "الكاتب نفسه (أو بوت)"
        if message.guild.me.guild_permissions.view_audit_log:
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                    deleter = entry.user.mention
                    break
                    
        embed.add_field(name="المشرف الذي حذفها:", value=deleter, inline=False)
        embed.add_field(name="المحتوى (صندوق أسود):", value=f"```\n{message.content or 'لا يوجد نص'}\n```", inline=False)
        await self.send_webhook_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        embed = discord.Embed(
            title="⚠️ تحذير: نشاط مكثف (مسح جماعي)", 
            description=f"تم مسح **{len(payload.message_ids)}** رسالة دفعة واحدة في قناة {channel.mention} 🧹",
            color=discord.Color.brand_red()
        )
        await self.send_webhook_log(guild, embed)

    # ---------------- 4. سجلات وقائيات القنوات ----------------
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(title="🧨 حذف قناة", color=discord.Color.dark_red())
        embed.add_field(name="القناة المحذوفة:", value=channel.name, inline=True)
        
        if "ticket" in channel.name.lower():
            embed.description = "⚠️ **تنبيه: هذه القناة تبدو كتذكرة دعم فني!**"
            
        view = RestoreChannelView(channel.name, channel.type, channel.category.id if channel.category else None)
        await self.send_webhook_log(channel.guild, embed, view=view)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.name != after.name or before.topic != after.topic:
            embed = discord.Embed(title="📝 تعديل إعدادات قناة", color=discord.Color.orange())
            embed.add_field(name="القناة:", value=after.mention, inline=False)
            if before.name != after.name:
                embed.add_field(name="الاسم:", value=f"القديم: `{before.name}`\nالجديد: `{after.name}`")
            if hasattr(before, 'topic') and before.topic != after.topic:
                embed.add_field(name="الوصف (Topic):", value="تم تغييره.", inline=False)
            await self.send_webhook_log(after.guild, embed)

    # ---------------- 5. سجلات السيرفر (الصلاحيات والدعوات) ----------------

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        if before.permissions != after.permissions:
            embed = discord.Embed(title="🛡️ تعديل صلاحيات رتبة حساسة", color=discord.Color.yellow())
            embed.add_field(name="الرتبة:", value=after.mention, inline=False)
            
            b_perms = dict(before.permissions)
            a_perms = dict(after.permissions)
            
            added = [p for p, v in a_perms.items() if v and not b_perms.get(p)]
            removed = [p for p, v in b_perms.items() if v and not a_perms.get(p)]
            
            desc = ""
            if added: desc += "🟢 **تم إضافة صلاحيات:**\n" + "\n".join([f"+ {p.replace('_', ' ').title()}" for p in added]) + "\n\n"
            if removed: desc += "🔴 **تم سحب صلاحيات:**\n" + "\n".join([f"- {p.replace('_', ' ').title()}" for p in removed])
            
            embed.description = f"```diff\n{desc}\n```" if desc else "تم تعديل صلاحيات عامة."
            await self.send_webhook_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        embed = discord.Embed(title="🔗 إنشاء دعوة جديدة", color=discord.Color.blurple())
        embed.add_field(name="الرابط:", value=invite.url)
        embed.add_field(name="أنشأها:", value=invite.inviter.mention if invite.inviter else "غير معروف")
        embed.add_field(name="القناة:", value=invite.channel.mention)
        await self.send_webhook_log(invite.guild, embed)


async def setup(bot):
    await bot.add_cog(EventsHandler(bot))
