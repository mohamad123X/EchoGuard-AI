import discord
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio

# ==========================================
# 🟩 نظام التحقق (Verification System) 🟩
# ==========================================

# 1. زر التحقق الذي يظهر للأعضاء
class VerificationPanelView(View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id # الرتبة التي سيأخذها العضو

    # custom_id ديناميكي لكي يعمل حتى بعد إعادة التشغيل (يحتوي على ID الرتبة)
    @discord.ui.button(label="☑️ تأكيد هويتك", style=discord.ButtonStyle.secondary, custom_id="verify_captcha_btn")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        # الخطوة 1: إرسال الكابتشا الوهمية (رسالة مخفية)
        await interaction.response.send_message("🔄 **جاري التحقق من هويتك... الرجاء الانتظار.**", ephemeral=True)
        
        # الخطوة 2: الانتظار 3 ثوانٍ (محاكاة الدوران)
        await asyncio.sleep(3)
        
        # الخطوة 3: إعطاء الرتبة
        role = interaction.guild.get_role(self.role_id)
        if role:
            try:
                await interaction.user.add_roles(role)
                # الخطوة 4: تحديث الرسالة إلى اللون الأخضر/النجاح
                await interaction.edit_original_response(content="✅ **لقد تم إثبات هويتك بنجاح!**\n(اضغط على 'إلغاء' أو Dismiss لإغلاق هذه الرسالة)")
            except discord.Forbidden:
                await interaction.edit_original_response(content="❌ **حدث خطأ:** صلاحيات البوت أقل من الرتبة المحددة. يرجى رفع رتبة البوت في الإعدادات.")
        else:
            await interaction.edit_original_response(content="❌ **حدث خطأ:** الرتبة لم تعد موجودة في السيرفر.")

# 2. واجهة اختيار الرتبة (من قبل الإدارة)
class VerificationRoleSelectView(View):
    def __init__(self, bot, target_channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.bot = bot
        self.target_channel = target_channel

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="🛡️ اختر الرتبة التي سيحصل عليها العضو...",
        min_values=1, max_values=1
    )
    async def select_role(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        selected_role = select.values[0]
        
        # إنشاء بانر التحقق
        embed = discord.Embed(
            title="🛡️ نظام الحماية والتحقق",
            description="للوصول إلى باقي قنوات السيرفر، يرجى الضغط على الزر أدناه لإثبات أنك لست روبوتاً.",
            color=discord.Color.from_str("#00f2ff")
        )
        embed.set_image(url="https://i.postimg.cc/rwDLrvZ4/Minecraft-banner.jpg")
        
        # إرسال لوحة التحقق للقناة المحددة
        # نمرر ID الرتبة لنستخدمه في الزر
        # ملاحظة: في المشاريع الحقيقية يُفضل حفظ الرتبة في قاعدة البيانات بدل تمريرها مباشرة، لكن هذه الطريقة أسرع للتنفيذ.
        await self.target_channel.send(embed=embed, view=VerificationPanelView(selected_role.id))
        
        # لحفظ الرتبة في قاعدة البيانات لكي نعمل لها Setup في main.py لاحقاً
        guild_id = interaction.guild.id
        if guild_id not in self.bot.db: self.bot.db[guild_id] = {}
        self.bot.db[guild_id]['verify_role'] = selected_role.id

        await interaction.response.edit_message(content=f"✅ **تم إعداد نظام التحقق بنجاح في {self.target_channel.mention}!**", view=None)

# 3. واجهة إعداد التحقق (اختيار/إنشاء قناة)
class VerificationSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text],
        placeholder="1️⃣ اختر قناة التحقق الموجودة...", min_values=1, max_values=1
    )
    async def select_existing_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        selected_channel = select.values[0]
        await interaction.response.send_message("✅ ممتاز. الآن **اختر الرتبة** التي سيأخذها العضو بعد التحقق:", view=VerificationRoleSelectView(self.bot, selected_channel), ephemeral=True)

    @discord.ui.button(label="2️⃣ أو إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success, row=1)
    async def create_new_channel(self, interaction: discord.Interaction, button: Button):
        class NewVerificationModal(Modal, title="إنشاء قناة التحقق"):
            channel_name = TextInput(label="اسم القناة (اختياري)", placeholder="مثال: 🛡・التحقق", required=False)
            def __init__(self, bot):
                super().__init__()
                self.bot = bot
            async def on_submit(self, modal_inter: discord.Interaction):
                name = self.channel_name.value.strip() or "🛡・التحقق"
                overwrites = {
                    modal_inter.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_message_history=True),
                    modal_inter.guild.me: discord.PermissionOverwrite(send_messages=True, embed_links=True)
                }
                new_channel = await modal_inter.guild.create_text_channel(name, overwrites=overwrites)
                await modal_inter.response.send_message("✅ تم إنشاء القناة. الآن **اختر الرتبة** للتحقق:", view=VerificationRoleSelectView(self.bot, new_channel), ephemeral=True)
        await interaction.response.send_modal(NewVerificationModal(self.bot))


# ==========================================
# 🟪 نظام التذاكر (Ticket System) 🟪
# ==========================================
class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="📩 فتح تذكرة", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn_primary")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏳ جاري فتح تذكرتك السرية... (سيتم برمجتها لاحقاً)", ephemeral=True)

class TicketSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def send_ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎫 مركز الدعم الفني",
            description="للتواصل مع الإدارة، اضغط على الزر أدناه لفتح تذكرة خاصة بك.",
            color=discord.Color.from_str("#7000ff")
        )
        embed.set_image(url="https://i.postimg.cc/fb3TM3Qg/Ticket-Banner-Discord-Purple-Aesthetic.jpg") # البانر الجديد
        await channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message(f"✅ تم تفعيل التذاكر في {channel.mention}!", ephemeral=True)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text],
        placeholder="1️⃣ اختر قناة التذاكر الموجودة...", min_values=1, max_values=1
    )
    async def select_existing_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        await self.send_ticket_panel(interaction, select.values[0])

    @discord.ui.button(label="2️⃣ أو إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success, row=1)
    async def create_new_channel(self, interaction: discord.Interaction, button: Button):
        class NewTicketModal(Modal, title="إنشاء قناة التذاكر"):
            channel_name = TextInput(label="اسم القناة (اختياري)", placeholder="مثال: 📩・التذاكر", required=False)
            def __init__(self, parent_view):
                super().__init__()
                self.parent_view = parent_view
            async def on_submit(self, modal_inter: discord.Interaction):
                name = self.channel_name.value.strip() or "🎫・التذاكر"
                overwrites = {
                    modal_inter.guild.default_role: discord.PermissionOverwrite(send_messages=False),
                    modal_inter.guild.me: discord.PermissionOverwrite(send_messages=True, embed_links=True)
                }
                new_channel = await modal_inter.guild.create_text_channel(name, overwrites=overwrites)
                await self.parent_view.send_ticket_panel(modal_inter, new_channel)
        await interaction.response.send_modal(NewTicketModal(self))


# ==========================================
# 🟦 نظام الترحيب (Welcome System) 🟦
# ==========================================
# (الكود السابق الخاص بك كما هو مع اختصاره لترتيب الملف)
class RulesSelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="📌 اختر قناة القوانين...")
    async def select_rules(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        self.bot.db[interaction.guild.id]['rules_channel'] = select.values[0].id
        await interaction.response.edit_message(content="🎉 **تم إعداد نظام الترحيب بنجاح!**", view=None)

class WelcomeDataModal(Modal, title="تفاصيل رسالة الترحيب"):
    server_name = TextInput(label="اسم السيرفر", placeholder="مجتمعنا...", required=True)
    banner_url = TextInput(label="رابط بنر الترحيب (اختياري)", required=False)
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot, self.welcome_channel_id = bot, channel_id
    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.bot.db: self.bot.db[guild_id] = {}
        self.bot.db[guild_id]['welcome_channel'] = self.welcome_channel_id
        self.bot.db[guild_id]['server_name'] = self.server_name.value
        self.bot.db[guild_id]['banner_url'] = self.banner_url.value or "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg"
        await interaction.response.send_message("✅ خطوة أخيرة: **اختر قناة القوانين**:", view=RulesSelectView(self.bot), ephemeral=True)

class WelcomeSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="1️⃣ اختر قناة للترحيب...")
    async def select_existing_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        await interaction.response.send_modal(WelcomeDataModal(self.bot, select.values[0].id))
    @discord.ui.button(label="2️⃣ إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success, row=1)
    async def create_new_channel(self, interaction: discord.Interaction, button: Button):
        class NewChannelModal(Modal, title="إنشاء قناة ترحيب"):
            channel_name = TextInput(label="اسم القناة", required=False)
            async def on_submit(self, modal_inter: discord.Interaction):
                name = self.channel_name.value.strip() or "✨・الترحيب"
                overwrites = { modal_inter.guild.default_role: discord.PermissionOverwrite(send_messages=False) }
                new_channel = await modal_inter.guild.create_text_channel(name, overwrites=overwrites)
                await modal_inter.response.send_modal(WelcomeDataModal(interaction.client, new_channel.id))
        await interaction.response.send_modal(NewChannelModal())


# ==========================================
# ⚙️ لوحة التحكم الرئيسية (Dashboard) ⚙️
# ==========================================
class DashboardView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="إعداد الترحيب 👋", style=discord.ButtonStyle.primary, custom_id="setup_welcome")
    async def setup_welcome_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("اختر طريقة إعداد قناة الترحيب:", view=WelcomeSetupView(self.bot), ephemeral=True)

    @discord.ui.button(label="إعداد التذاكر 🎫", style=discord.ButtonStyle.secondary, custom_id="setup_tickets")
    async def setup_tickets_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⚙️ **إعداد نظام التذاكر:**", view=TicketSetupView(self.bot), ephemeral=True)

    @discord.ui.button(label="إعداد التحقق 🛡️", style=discord.ButtonStyle.success, custom_id="setup_verification")
    async def setup_verify_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⚙️ **إعداد نظام التحقق (Captcha):**", view=VerificationSetupView(self.bot), ephemeral=True)
