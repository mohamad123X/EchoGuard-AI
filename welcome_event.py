@commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g_id = str(member.guild.id) 
        data = self.bot.db.get(g_id, {})
        
        # الرتبة التلقائية
        auto_role_id = data.get('auto_role')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try: await member.add_roles(role)
                except Exception: pass
                
        # ================== رسالة الترحيب الجديدة المتطابقة مع الصورة ==================
        welcome_channel_id = data.get('welcome_channel')
        channel = member.guild.get_channel(welcome_channel_id)
        if channel:
            # يمكنك وضع رابط بانر البكسل آرت الخاص بك هنا
            banner_url = data.get('banner_url') or "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg" 
            
            # بناء النص كما في الصورة تماماً
            desc = (
                f"**Welcome** {member.mention} **to {member.guild.name}!**\n"
                f"You are member **{member.guild.member_count}** 🎉\n"
                "------------------------------------------------\n"
                "📌 Please read the `#rules`\n"  # يمكنك استبدال '#rules' بـ '<#123456789>' مع وضع آيدي قناة القوانين لتصبح قابلة للضغط
                "💬 Chat & have fun\n"
                "🚀 Enjoy"
            )

            # إنشاء الـ Embed مع اللون والتوقيت الزمني
            embed = discord.Embed(
                description=desc, 
                color=discord.Color.from_str("#1a3d36"), # لون أخضر غامق مقارب لطرف الصورة الأيسر
                timestamp=datetime.now(timezone.utc) # لإضافة التوقيت في الأسفل
            )
            
            # إضافة البانر الكبير
            embed.set_image(url=banner_url)
            
            # إضافة الصورة المصغرة في الزاوية العلوية (استخدمنا صورة السيرفر، وإذا لم توجد نستخدم صورة البوت/العضو)
            if
