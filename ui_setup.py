import discord
from discord.ui import View, Button, Select, Modal, TextInput

# ==========================================
# 3. نافذة إدخال بيانات الترحيب (اسم السيرفر والبنر)
# ==========================================
class WelcomeDataModal(Modal, title="تفاصيل رسالة الترحيب"):
    server_name = TextInput(
        label="اسم السيرفر (ليظهر في الترحيب)",
        placeholder="مثال: مجتمع المطورين...",
        required=True
    )
    banner_url = TextInput(
        label="رابط بنر الترحيب (اختياري)",
        placeholder="ضع الرابط هنا، أو اتركه فارغاً للصورة الافتراضية",
        required=False
    )

    def __init__(self, bot, welcome_channel_id):
        super().__init__()
        self.bot = bot
        self.welcome_channel_id = welcome_channel_id

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.bot.db:
            self.bot.db[guild_id] = {}
        
        # حفظ البيانات في قاعدة البيانات
        self.bot.db[guild_id]['welcome_channel'] = self.welcome_channel_id
        self.bot.db[guild_id]['server_name'] = self.server_name.value
        self.bot.db[guild_id]['banner_url'] = self.banner_url.value or "https://i.postimg.cc/1Xd9qsSy/download-(14).jpg"

        # الآن نطلب تحديد قناة القوانين عبر قائمة منسدلة
        await interaction.response.send_message("✅ تم الحفظ! خطوة أخيرة: **اختر قناة القوانين** من القائمة أدناه:", view=RulesSelectView(self.bot), ephemeral=True)

# ==========================================
# 2. الواجهة لاختيار قناة الترحيب أو إنشاء واحدة
# ==========================================
class WelcomeSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    # القائمة المنسدلة لاختيار قناة موجودة
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="1️⃣ اختر قناة موجودة للترحيب...",
        min_values=1,
        max_values=1
    )
    async def select_existing_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        # المستخدم اختار قناة موجودة. ننتقل لجمع اسم السيرفر
        selected_channel = select.values[0]
        await interaction.response.send_modal(WelcomeDataModal(self.bot, selected_channel.id))

    # الزر لإنشاء قناة جديدة (مفصول تماماً عن القائمة لمنع الأخطاء)
    @discord.ui.button(label="2️⃣ أو إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success, row=1)
    async def create_new_channel(self, interaction: discord.Interaction, button: Button):
        # نفتح نافذة لكتابة اسم القناة
        class NewChannelModal(Modal, title="إنشاء قناة ترحيب جديدة"):
            channel_name = TextInput(
                label="اسم القناة (اختياري)",
                placeholder="اتركه فارغاً وسأقوم باختيار اسم راقٍ...",
                required=False
            )
            
            async def on_submit(self, modal_inter: discord.Interaction):
                # إذا تركها المستخدم فارغة، نستخدم اسماً مميزاً
                name = self.channel_name.value.strip()
                if not name:
                    name = "✨・الترحيب"

                # إعداد صلاحيات القناة: الأعضاء لا يمكنهم الكتابة، البوت فقط يكتب
                overwrites = {
                    modal_inter.guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False),
                    modal_inter.guild.me: discord.PermissionOverwrite(send_messages=True, embed_links=True, attach_files=True)
                }
                
                # إنشاء القناة
                new_channel = await modal_inter.guild.create_text_channel(name, overwrites=overwrites)
                
                # إرسال المودل التالي الخاص باسم السيرفر
                await modal_inter.response.send_modal(WelcomeDataModal(interaction.client, new_channel.id))
        
        await interaction.response.send_modal(NewChannelModal())

# ==========================================
# 4. قائمة منسدلة لاختيار قناة القوانين (الخطوة الأخيرة)
# ==========================================
class RulesSelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="📌 اختر قناة القوانين..."
    )
    async def select_rules(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        guild_id = interaction.guild.id
        self.bot.db[guild_id]['rules_channel'] = select.values[0].id
        await interaction.response.edit_message(content="🎉 **تم إعداد نظام الترحيب بنجاح! البوت جاهز الآن للترحيب بالأعضاء الجدد.**", view=None)

# ==========================================
# 1. لوحة التحكم الرئيسية (التي تظهر في القناة المخفية)
# ==========================================
class DashboardView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="إعداد نظام الترحيب ⚙️", style=discord.ButtonStyle.primary, custom_id="setup_welcome")
    async def setup_welcome_btn(self, interaction: discord.Interaction, button: Button):
        # نرسل رسالة مخفية تحتوي على خيارات الترحيب
        await interaction.response.send_message(
            "اختر طريقة إعداد قناة الترحيب:\nيمكنك اختيار قناة من القائمة، أو الضغط على الزر لإنشاء واحدة جديدة كلياً.",
            view=WelcomeSetupView(self.bot),
            ephemeral=True
        )
