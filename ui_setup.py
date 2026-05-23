import discord
from discord.ui import View, Button, Modal, TextInput
from ticket_system import TicketSetupView

# --- 1. لوحة التحكم الرئيسية ---
class DashboardView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="إعداد الترحيب 👋", style=discord.ButtonStyle.primary, custom_id="setup_welcome")
    async def setup_welcome_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="👋 إعداد نظام الترحيب",
            description="الرجاء اختيار القناة التي تريد أن يرسل فيها البوت رسائل الترحيب بالأعضاء الجدد:",
            color=discord.Color.from_str("#00f2ff")
        )
        await interaction.response.send_message(embed=embed, view=WelcomeSetupView(self.bot), ephemeral=True)

    @discord.ui.button(label="إعداد التذاكر 🎫", style=discord.ButtonStyle.secondary, custom_id="setup_tickets")
    async def setup_tickets_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="⚙️ إعداد نظام التذاكر",
            description="الرجاء اختيار القناة التي تريد وضع رسالة التذاكر فيها، أو إنشاء قناة جديدة:",
            color=discord.Color.from_str("#7000ff")
        )
        await interaction.response.send_message(embed=embed, view=TicketSetupView(), ephemeral=True)

    @discord.ui.button(label="إعداد التحقق 🛡️", style=discord.ButtonStyle.success, custom_id="setup_verification")
    async def setup_verify_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🛡️ إعداد نظام التحقق (Captcha)",
            description="الرجاء اختيار القناة التي ستكون مخصصة للتحقق (يجب أن تكون القناة الوحيدة التي يراها العضو الجديد):",
            color=discord.Color.from_str("#00ff00")
        )
        await interaction.response.send_message(embed=embed, view=VerificationSetupView(), ephemeral=True)


# --- 2. إعداد الترحيب ---
class WelcomeSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="اختر قناة الترحيب...")
    async def select_welcome_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        selected_channel = select.values[0]
        
        # حفظ القناة في قاعدة البيانات المؤقتة
        if interaction.guild.id not in self.bot.db:
            self.bot.db[interaction.guild.id] = {}
        self.bot.db[interaction.guild.id]['welcome_channel'] = selected_channel.id
        
        await interaction.response.send_message(f"✅ تم ربط نظام الترحيب بقناة {selected_channel.mention} بنجاح! الألوان والصور جاهزة للعمل عند دخول أي عضو.", ephemeral=True)


# --- 3. إعداد التحقق (Verification) ---
class VerificationSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="اختر قناة التحقق...")
    async def select_verify_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        
        embed = discord.Embed(
            title="🛡️ نظام الحماية والتحقق",
            description="> **مرحباً بك في السيرفر!**\n> لحماية المجتمع من الروبوتات (Bots)، يرجى الضغط على الزر أدناه لإثبات هويتك والوصول إلى باقي القنوات.",
            color=discord.Color.from_str("#00ff00")
        )
        # صورة خاصة بنظام التحقق (يمكنك تغيير الرابط)
        embed.set_image(url="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1000&auto=format&fit=crop") 
        
        await channel.send(embed=embed, view=VerificationPanelView())
        await interaction.response.send_message(f"✅ تم إرسال لوحة التحقق إلى {channel.mention} بنجاح!", ephemeral=True)


# --- 4. لوحة التحقق (تظهر للأعضاء) ---
class VerificationPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="☑️ تأكيد هويتك", style=discord.ButtonStyle.success, custom_id="verify_member_btn_final")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        # البحث عن رتبة اسمها "Verified" أو إنشاء واحدة جديدة
        role = discord.utils.get(interaction.guild.roles, name="Verified")
        if not role:
            try:
                role = await interaction.guild.create_role(name="Verified", color=discord.Color.green())
            except discord.Forbidden:
                return await interaction.response.send_message("❌ لا أملك صلاحية لإنشاء رتبة التحقق! يرجى رفع رتبة البوت.", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.response.send_message("أنت موثق بالفعل! لا حاجة للضغط مرة أخرى. ✅", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🎉 تم التحقق بنجاح! لقد حصلت على صلاحية الدخول للسيرفر.", ephemeral=True)
