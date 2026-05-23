@commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g_id = str(member.guild.id) 
        data = self.bot.db.get(g_id, {})
        
        # 1. نظام الرتبة التلقائية عند الدخول
        auto_role_id = data.get('auto_role')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try: 
                    await member.add_roles(role)
                except Exception: 
                    pass
                
        # 2. رسالة الترحيب المتطابقة مع الصورة تماماً
        welcome_channel_id = data.get('welcome_channel')
        channel = member.guild.get_channel(welcome_channel_id)
        if channel:
            # جلب رابط البانر من القاعدة أو وضع رابط افتراضي
            banner_url = data.get('banner_url') or "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg" 
            
            # بناء نص الترحيب متضمناً منشن العضو، اسم السيرفر تلقائياً، وعدد الأعضاء
            desc = (
                f"**Welcome** {member.mention} **to {member.guild.name}!**\n\n"
                f"You are member **{member.guild.member_count}** 🎉\n"
                "--------------------------------------------------\n"
                "📌 Please read the `#rules`\n"  # نصيحة: استبدل '#rules' بـ <#آيدي_قناة_القوانين> لتصبح قابلة للضغط
                "💬 Chat & have fun\n"
                "🚀 Enjoy"
            )

            # إنشاء الـ Embed باللون الداكن المناسب مع التوقيت الزمني في الأسفل
            embed = discord.Embed(
                description=desc, 
                color=discord.Color.from_str("#1a3d36"), # لون متناسق مع السيرفرات الداكنة
                timestamp=datetime.now(timezone.utc)     # لإظهار وقت الدخول أسفل الرسالة
            )
            
            # وضع صورة البانر الكبيرة في الأسفل
            embed.set_image(url=banner_url)
            
            # وضع شعار/أيقونة السيرفر تلقائياً كصورة مصغرة في الزاوية العلوية اليمنى
            if member.guild.icon:
                embed.set_thumbnail(url=member.guild.icon.url)
            
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

        # 3. سجل الحماية الداخلي للإدارة (كشف الحسابات الوهمية)
        acc_age = (datetime.now(timezone.utc) - member.created_at).days
        embed_log = discord.Embed(title="📥 دخول عضو", color=discord.Color.green())
        embed_log.add_field(name="العضو:", value=f"{member.mention} ({member.name})")
        embed_log.add_field(name="حالة الحساب:", value="🔴 **حساب جديد (وهمي؟)**" if acc_age < 7 else f"🟢 آمن (منذ {acc_age} يوم)")
        await self.send_webhook_log(member.guild, embed_log, view=UserProfileView(member))
