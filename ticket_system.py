import discord
from discord.ui import View, Button, Modal, TextInput

class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 فتح تذكرة دعم", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn_primary")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        # جلب تصنيف التذاكر أو إنشائه
        category = discord.utils.get(interaction.guild.categories, name="التذاكر المفتوحة")
        if not category:
            category = await interaction.guild.create_category("التذاكر المفتوحة")

        # إعداد الصلاحيات (الإدارة والمستخدم فقط)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_channel = await interaction.guild.create_text_channel(
            f"ticket-{interaction.user.name}", 
            category=category, 
            overwrites=overwrites
        )
        
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)
        
        # رسالة الترحيب داخل التذكرة
        embed = discord.Embed(
            title="🎫 تذكرة دعم فني",
            description=f"مرحباً بك {interaction.user.mention}!\nيرجى طرح مشكلتك أو استفسارك هنا، وسيقوم فريق الدعم بالرد عليك في أقرب وقت.",
            color=discord.Color.from_str("#7000ff")
        )
        await ticket_channel.send(embed=embed)


class TicketSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def send_ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎫 مركز الدعم والمساعدة | Support Center",
            description="> **هل تواجه مشكلة أو تحتاج إلى مساعدة؟**\n> يرجى الضغط على الزر أدناه لفتح تذكرة خاصة والتواصل بشكل مباشر مع فريق الإدارة.",
            color=discord.Color.from_str("#7000ff")
        )
        embed.set_image(url="https://i.postimg.cc/1Xd9qsSy/download-(14).jpg") 
        
        await channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message(f"✅ تم إعداد لوحة التذاكر بنجاح في القناة: {channel.mention}", ephemeral=True)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="1️⃣ اختر قناة التذاكر الموجودة...",
        min_values=1,
        max_values=1
    )
    async def select_existing_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        selected_channel = select.values[0]
        await self.send_ticket_panel(interaction, selected_channel)

    @discord.ui.button(label="2️⃣ أو إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success, row=1)
    async def create_new_channel(self, interaction: discord.Interaction, button: Button):
        
        class NewTicketModal(Modal, title="إنشاء قناة التذاكر"):
            channel_name = TextInput(
                label="اسم القناة",
                placeholder="مثال: 📩・التذاكر",
                default="🎫・التذاكر",
                required=False
            )
            
            def __init__(self, parent_view: TicketSetupView):
                super().__init__()
                self.parent_view = parent_view

            async def on_submit(self, modal_inter: discord.Interaction):
                name = self.channel_name.value.strip() or "🎫・التذاكر"
                overwrites = {
                    modal_inter.guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False),
                    modal_inter.guild.me: discord.PermissionOverwrite(send_messages=True, embed_links=True)
                }
                new_channel = await modal_inter.guild.create_text_channel(name, overwrites=overwrites)
                await self.parent_view.send_ticket_panel(modal_inter, new_channel)
        
        await interaction.response.send_modal(NewTicketModal(self))
