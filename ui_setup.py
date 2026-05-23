import discord
from discord.ui import View, Button, Modal, TextInput
from ticket_system import TicketSetupView
from giveaway_system import GiveawaySetupView

# --- لوحة التحكم الرئيسية ---
class DashboardView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="إعداد الترحيب 👋", style=discord.ButtonStyle.primary, custom_id="setup_welcome_main")
    async def setup_welcome_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="👋 إعداد نظام الترحيب المتطور",
            description="الرجاء استخدام القوائم أدناه لتحديد **قناة الترحيب** ثم **قناة القوانين** لتضمينها بشكل صحيح.",
            color=discord.Color.from_str("#ff00a0")
        )
        await interaction.response.send_message(embed=embed, view=WelcomeSetupView(self.bot), ephemeral=True)

    @discord.ui.button(label="إعداد التذاكر 🎫", style=discord.ButtonStyle.secondary, custom_id="setup_tickets_main")
    async def setup_tickets_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="⚙️ إعداد نظام التذاكر",
            description="الرجاء اختيار قناة وضع رسالة التذاكر للأعضاء:",
            color=discord.Color.from_str("#7000ff")
        )
        await interaction.response.send_message(embed=embed, view=TicketSetupView(), ephemeral=True)

    @discord.ui.button(label="إعداد التحقق 🛡️", style=discord.ButtonStyle.success, custom_id="setup_verification_main")
    async def setup_verify_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🛡️ إعداد نظام التحقق البشري (Captcha)",
            description="اختر القناة المخصصة للتحقق (التي تظهر للجدد فقط):",
            color=discord.Color.from_str("#00ff00")
        )
        await interaction.response.send_message(embed=embed, view=VerificationSetupView(), ephemeral=True)

    @discord.ui.button(label="سجل الأحداث ⚙️", style=discord.ButtonStyle.danger, custom_id="setup_logs_main")
    async def setup_logs_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="⚙️ إعداد نظام السجلات (Log System)",
            description="اختر القناة السرية التي سيرسل إليها البوت تقارير السيرفر (حذف وتعديل الرسائل، دخول وخروج الروم الصوتي، تعديل الرتب):",
            color=discord.Color.from_str("#ffaa00")
        )
        await interaction.response.send_message(embed=embed, view=LogSetupView(self.bot), ephemeral=True)

    @discord.ui.button(label="رتبة تلقائية 🏷️", style=discord.ButtonStyle.primary, custom_id="setup_autorole_main")
    async def setup_autorole_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🏷️ إعداد الرتبة التلقائية (Auto-Role)",
            description="اختر الرتبة التي تمنح تلقائياً للأعضاء فور دخولهم السيرفر:",
            color=discord.Color.from_str("#ffff00")
        )
        await interaction.response.send_message(embed=embed, view=AutoRoleSetupView(self.bot), ephemeral=True)

    @discord.ui.button(label="الرد التلقائي 💬", style=discord.ButtonStyle.secondary, custom_id="setup_autoresponder_main")
    async def setup_autoresponder_btn(self, interaction: discord.Interaction, button: Button):
        class AutoResponderModal(Modal, title="إضافة رد تلقائي ذكي"):
            keyword = TextInput(label="الكلمة المفتاحية (مثال: السلام عليكم)", placeholder="اكتب الجملة هنا...", required=True)
            response = TextInput(label="رد البوت (مثال: وعليكم السلام ورحمة الله)", placeholder="اكتب رد البوت هنا...", style=discord.TextStyle.paragraph, required=True)
            
            def __init__(self, bot_obj):
                super().__init__()
                self.bot = bot_obj

            async def on_submit(self, modal_inter: discord.Interaction):
                g_id = modal_inter.guild.id
                if g_id not in self.bot.db: self.bot.db[g_id] = {}
                if 'auto_responses' not in self.bot.db[g_id]: self.bot.db[g_id]['auto_responses'] = {}
                
                self.bot.db[g_id]['auto_responses'][self.keyword.value.strip()] = self.response.value.strip()
                await modal_inter.response.send_message(f"✅ تم حفظ الرد بنجاح! عندما يكتب شخص `{self.keyword.value}` سيرد البوت تلقائياً.", ephemeral=True)

        await interaction.response.send_modal(AutoResponderModal(self.bot))

    @discord.ui.button(label="نظام المسابقات 🎉", style=discord.ButtonStyle.success, custom_id="setup_giveaways_main")
    async def setup_giveaways_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🎉 إعداد نظام المسابقات (Giveaways)",
            description="الآن سنقوم بإنشاء غرف المسابقات المخصصة للادارة والأعضاء.",
            color=discord.Color.from_str("#ff0000")
        )
        await interaction.response.send_message(embed=embed, view=GiveawaySetupView(self.bot), ephemeral=True)


# --- واجهة إعداد الترحيب وإصلاح المشاكل السابقة ---
class WelcomeSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="1️⃣ اختر قناة الترحيب بالأعضاء...", custom_id="wel_select_chan")
    async def select_welcome_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        g_id = interaction.guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['welcome_channel'] = select.values[0].id
        await interaction.response.send_message("✅ تم تحديد قناة الترحيب بنجاح! الآن اختر قناة القوانين من القائمة نفسها أدناه.", ephemeral=True)

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="2️⃣ اختر قناة القوانين (Rules)...", custom_id="wel_select_rules")
    async def select_rules_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        g_id = interaction.guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['rules_channel'] = select.values[0].id
        
        # بعد تحديد القوانين، نتيح له خيار إضافة بنر أو إنهاء الإعداد
        class BannerModal(Modal, title="إضافة رابط بنر مخصص"):
            url = TextInput(label="رابط الصورة/البانر (اتركه فارغاً لافتراضي فخم)", required=False, placeholder="https://...")
            def __init__(self, bot_obj):
                super().__init__()
                self.bot = bot_obj
            async def on_submit(self, modal_inter: discord.Interaction):
                img = self.url.value.strip() or "https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?q=80&w=1000&auto=format&fit=crop"
                self.bot.db[modal_inter.guild.id]['banner_url'] = img
                await modal_inter.response.send_message("🎉 ممتاز! تم إعداد نظام الترحيب بالكامل (القناة، القوانين، والبنر المخصص جاهزون).", ephemeral=True)

        await interaction.response.send_modal(BannerModal(self.bot))


# --- واجهة إعداد التحقق ---
class VerificationSetupView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="اختر قناة التحقق لحماية السيرفر...")
    async def select_verify_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        embed = discord.Embed(
            title="🛡️ بوابة التحقق الآمنة | Verification Gate",
            description="> **مرحباً بك في مجتمعنا!**\n> اضغط على الزر أدناه لتأكيد هويتك وتفادي أنظمة الحظر التلقائي للروبوتات والمخربين.",
            color=discord.Color.from_str("#00ff00")
        )
        embed.set_image(url="https://images.unsplash.com/photo-1563986768609-322da13575f3?q=80&w=1000&auto=format&fit=crop")
        await channel.send(embed=embed, view=VerificationPanelView())
        await interaction.response.send_message(f"✅ تم تفعيل ونشر نظام التحقق في قناة: {channel.mention}", ephemeral=True)

class VerificationPanelView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="☑️ تأكيد هويتك ودخول السيرفر", style=discord.ButtonStyle.success, custom_id="verify_member_btn_final")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        role = discord.utils.get(interaction.guild.roles, name="Verified")
        if not role:
            try: role = await interaction.guild.create_role(name="Verified", color=discord.Color.green())
            except discord.Forbidden: return await interaction.response.send_message("❌ لا أمتلك صلاحيات لإنشاء رتبة `Verified`!", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.response.send_message("أنت عضو موثق ومعتمد بالسيرفر بالفعل! ✅", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🎉 تم التحقق بنجاح! حصلت على رتبة الموثقين وفتحت لك القنوات.", ephemeral=True)


# --- واجهة إعداد السجلات (Logs) ---
class LogSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="اختر قناة السجلات والتقارير...")
    async def select_log_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        g_id = interaction.guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['log_channel'] = select.values[0].id
        await interaction.response.send_message(f"⚙️ تم تفعيل سجل الأحداث الفوري بنجاح في قناة: {select.values[0].mention}", ephemeral=True)


# --- واجهة إعداد الرتبة التلقائية ---
class AutoRoleSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="اختر الرتبة التلقائية للأعضاء الجدد...")
    async def select_auto_role(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        g_id = interaction.guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['auto_role'] = select.values[0].id
        await interaction.response.send_message(f"🏷️ تم تعيين رتبة {select.values[0].name} لتُعطى تلقائياً لأي عضو ينضم للسيرفر!", ephemeral=True)
