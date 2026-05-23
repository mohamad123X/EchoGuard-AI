import discord
from discord.ui import View, Button, Modal, TextInput

# --- 1. واجهة العضو ---
class TicketCategorySelectView(View):
    def __init__(self, categories):
        super().__init__(timeout=None)
        if not categories:
            categories = ["دعم عام"]
            
        options = [discord.SelectOption(label=cat, value=cat, emoji="📩") for cat in categories]
        select = discord.ui.Select(placeholder="اختر القسم المناسب لمشكلتك...", options=options, custom_id="ticket_category_dropdown")
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        category_name = interaction.data["values"][0]
        guild = interaction.guild
        
        discord_category = discord.utils.get(guild.categories, name="التذاكر المفتوحة")
        if not discord_category: 
            discord_category = await guild.create_category("التذاكر المفتوحة")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}", 
            category=discord_category, 
            overwrites=overwrites
        )
        
        await interaction.response.send_message(f"✅ تم فتح تذكرتك في قسم **{category_name}**: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🎫 تذكرة دعم فني - قسم ({category_name})",
            description=f"مرحباً بك {interaction.user.mention}!\nيرجى طرح مشكلتك المتعلقة بـ **{category_name}** هنا، وسيقوم الفريق بالرد عليك.",
            color=discord.Color.from_str("#7000ff")
        )
        await ticket_channel.send(embed=embed)


# --- 2. الزر الأساسي لفتح التذكرة ---
class TicketPanelView(View):
    def __init__(self, bot=None):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📩 فتح تذكرة", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn_primary")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        g_id = str(interaction.guild.id)
        bot_instance = self.bot or interaction.client
        categories = bot_instance.db.get(g_id, {}).get('ticket_categories', [])
        
        await interaction.response.send_message(
            "يرجى تحديد نوع التذكرة التي ترغب بفتحها من القائمة أدناه:", 
            view=TicketCategorySelectView(categories), 
            ephemeral=True
        )


# --- 3. واجهة الإدارة (تم الإصلاح) ---
class TicketSetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def send_ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎫 مركز الدعم والمساعدة | EchoGuard",
            description="> **هل تواجه مشكلة أو تحتاج إلى مساعدة؟**\n> يرجى الضغط على الزر أدناه لاختيار القسم المناسب وفتح تذكرة تواصل.",
            color=discord.Color.from_str("#7000ff")
        )
        # صورة التذاكر الافتراضية الخاصة بك
        embed.set_image(url="https://i.postimg.cc/fb3TM3Qg/Ticket-Banner-Discord-Purple-Aesthetic.jpg") 
        await channel.send(embed=embed, view=TicketPanelView(self.bot))
        await interaction.response.send_message(f"✅ تم إعداد لوحة التذاكر بنجاح في القناة: {channel.mention}", ephemeral=True)

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="1️⃣ اختر قناة التذاكر لوضع الرسالة...")
    async def select_existing_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        # الإصلاح: جلب كائن القناة الحقيقي
        channel = interaction.guild.get_channel(select.values[0].id)
        if not channel:
            return await interaction.response.send_message("❌ حدث خطأ في العثور على القناة.", ephemeral=True)
        await self.send_ticket_panel(interaction, channel)

    @discord.ui.button(label="➕ إضافة قسم تذاكر جديد", style=discord.ButtonStyle.success, row=1)
    async def add_category_btn(self, interaction: discord.Interaction, button: Button):
        class CategoryModal(Modal, title="إضافة قسم تذاكر للقائمة"):
            cat_name = TextInput(label="اسم القسم (مثال: دعم فني، شراء)", placeholder="اكتب اسم القسم هنا...", required=True)
            
            def __init__(self, bot_obj):
                super().__init__()
                self.bot = bot_obj

            async def on_submit(self, modal_inter: discord.Interaction):
                g_id = str(modal_inter.guild.id)
                if g_id not in self.bot.db: self.bot.db[g_id] = {}
                if 'ticket_categories' not in self.bot.db[g_id]: self.bot.db[g_id]['ticket_categories'] = []
                
                self.bot.db[g_id]['ticket_categories'].append(self.cat_name.value.strip())
                await modal_inter.response.send_message(f"✅ تم إضافة قسم التذاكر: **{self.cat_name.value}** بنجاح!", ephemeral=True)
                
        await interaction.response.send_modal(CategoryModal(self.bot))
