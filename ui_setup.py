import discord
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio

# ==========================================
# 🎫 نظام التذاكر المحدث (Ticket System)
# ==========================================
class TicketPanelView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📩 فتح تذكرة", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild_id = interaction.guild.id
        role_id = self.bot.db.get(guild_id, {}).get('ticket_role')
        role_mention = f"<@&{role_id}>" if role_id else "الإدارة"
        
        # إشعار الإدارة في قناة التحكم
        log_channel = discord.utils.get(interaction.guild.text_channels, name="⚙・لوحة-التحكم")
        if log_channel:
            await log_channel.send(f"🔔 **تذكرة جديدة!**\nفتح بواسطة: {interaction.user.mention}\nالمسؤولون المطلوبون: {role_mention}")
        
        await interaction.response.send_message("✅ تم فتح تذكرتك بنجاح!", ephemeral=True)

class TicketRoleSelectView(View):
    def __init__(self, bot, channel):
        super().__init__()
        self.bot, self.channel = bot, channel

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="🛡️ اختر رتبة الإدارة المسؤولة عن التذاكر...")
    async def select_role(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        role = select.values[0]
        guild_id = interaction.guild.id
        if guild_id not in self.bot.db: self.bot.db[guild_id] = {}
        self.bot.db[guild_id]['ticket_role'] = role.id
        
        embed = discord.Embed(title="🎫 مركز الدعم الفني", description="لفتح تذكرة، اضغط على الزر أدناه.", color=discord.Color.purple())
        embed.set_image(url="https://i.postimg.cc/fb3TM3Qg/Ticket-Banner-Discord-Purple-Aesthetic.jpg")
        await self.channel.send(embed=embed, view=TicketPanelView(self.bot))
        await interaction.response.edit_message(content=f"✅ تم تفعيل النظام في {self.channel.mention} مع الرتبة {role.mention}", view=None)

class TicketSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.select(cls=discord.ui.ChannelSelect, placeholder="1️⃣ اختر قناة التذاكر...")
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        await interaction.response.send_message("الآن اختر الرتبة التي سيصلها إشعار التذاكر:", view=TicketRoleSelectView(self.bot, select.values[0]), ephemeral=True)

# ==========================================
# 👋 نظام الترحيب المحدث (إصلاح التداخل)
# ==========================================
class WelcomeDataModal(Modal, title="تفاصيل الترحيب"):
    server_name = TextInput(label="اسم السيرفر", required=True)
    def __init__(self, bot, channel):
        super().__init__()
        self.bot, self.channel = bot, channel
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"مرحباً بك في {self.server_name.value}!", description="نتمنى لك وقتاً ممتعاً!", color=discord.Color.green())
        embed.set_image(url="https://i.postimg.cc/1Xd9qsSy/download-(14).jpg")
        await self.channel.send(embed=embed)
        await interaction.response.send_message("✅ تم إعداد القناة والترحيب بنجاح!", ephemeral=True)

class WelcomeSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    @discord.ui.button(label="إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success)
    async def create_new(self, interaction: discord.Interaction, button: Button):
        new_channel = await interaction.guild.create_text_channel("✨・الترحيب")
        await interaction.response.send_modal(WelcomeDataModal(self.bot, new_channel))

# ... (DashboardView وباقي الكود) ...
