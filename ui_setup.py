import discord
from discord.ui import View, Button, Modal, TextInput, ChannelSelect, RoleSelect

# 1. لوحة التحكم الرئيسية
class DashboardView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="إعداد الترحيب 👋", style=discord.ButtonStyle.primary, custom_id="setup_welcome")
    async def setup_welcome_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("جاري إعداد نظام الترحيب...", ephemeral=True)

    @discord.ui.button(label="إعداد التذاكر 🎫", style=discord.ButtonStyle.secondary, custom_id="setup_tickets")
    async def setup_tickets_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("جاري إعداد نظام التذاكر...", ephemeral=True)

    @discord.ui.button(label="إعداد التحقق 🛡️", style=discord.ButtonStyle.success, custom_id="setup_verification")
    async def setup_verify_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("جاري إعداد نظام التحقق...", ephemeral=True)

# 2. لوحة التذاكر
class TicketPanelView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📩 فتح تذكرة", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("تم فتح التذكرة!", ephemeral=True)

# 3. لوحة التحقق
class VerificationPanelView(View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="☑️ تأكيد هويتك", style=discord.ButtonStyle.secondary, custom_id="verify_captcha_btn")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("تم التحقق بنجاح!", ephemeral=True)
