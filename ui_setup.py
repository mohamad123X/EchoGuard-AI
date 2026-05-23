import discord
from discord.ui import View, Button
from ticket_system import TicketSetupView

class DashboardView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="إعداد الترحيب 👋", style=discord.ButtonStyle.primary, custom_id="setup_welcome")
    async def setup_welcome_btn(self, interaction: discord.Interaction, button: Button):
        # يمكننا لاحقاً إضافة Modal هنا لإعداد القناة والبانر
        await interaction.response.send_message("🛠️ سيتم قريباً ربط واجهة إعداد الترحيب المتقدمة!", ephemeral=True)

    @discord.ui.button(label="إعداد التذاكر 🎫", style=discord.ButtonStyle.secondary, custom_id="setup_tickets")
    async def setup_tickets_btn(self, interaction: discord.Interaction, button: Button):
        # استدعاء لوحة إعداد التذاكر الحقيقية
        embed = discord.Embed(
            title="⚙️ إعداد نظام التذاكر",
            description="الرجاء اختيار القناة التي تريد وضع رسالة التذاكر فيها، أو إنشاء قناة جديدة.",
            color=discord.Color.from_str("#7000ff")
        )
        await interaction.response.send_message(embed=embed, view=TicketSetupView(), ephemeral=True)

    @discord.ui.button(label="إعداد التحقق 🛡️", style=discord.ButtonStyle.success, custom_id="setup_verification")
    async def setup_verify_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🛡️ نظام الحماية (Captcha) قيد التجهيز!", ephemeral=True)
