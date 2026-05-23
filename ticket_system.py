import discord
from discord.ui import View, Button, Select, Modal, TextInput

# ==========================================
# 1. لوحة التذاكر (التي ستظهر للأعضاء في القناة)
# ==========================================
class TicketPanelView(View):
    def __init__(self):
        # timeout=None مهم جداً! يضمن أن الزر سيعمل حتى لو تم إطفاء البوت وتشغيله مجدداً
        super().__init__(timeout=None)

    # custom_id ضروري لربط الزر الدائم بالبوت
    @discord.ui.button(label="📩 فتح تذكرة (Open Ticket)", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn_primary")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        # هنا سنضع لاحقاً كود إنشاء قناة التذكرة الخاصة (Private Channel)
        await interaction.response.send_message("⏳ جاري فتح تذكرتك السرية...", ephemeral=True)

# ==========================================
# 2. إعداد لوحة التذاكر (من جهة الإدارة)
# ==========================================
class TicketSetupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    # وظيفة مشتركة لإرسال رسالة البانر والزر بعد تحديد القناة
    async def send_ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎫 مركز الدعم والمساعدة",
            description="إذا كنت تواجه أي مشكلة أو تحتاج إلى مساعدة، يرجى الضغط على الزر أدناه لفتح تذكرة خاصة والتواصل مع فريق الإدارة.",
            color=discord.Color.from_str("#7000ff") # لون نيون احترافي
        )
        
        # يمكنك استبدال هذا الرابط برابط الصورة المباشر للبانر الذي أرسلته لي
        embed.set_image(url="https://i.postimg.cc/1Xd9qsSy/download-(14).jpg") 
        
        # إرسال اللوحة مع زر فتح التذكرة
        await channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message(f"✅ تم إنشاء لوحة التذاكر بنجاح في {channel.mention}!", ephemeral=True)


    # الخيار الأول: قائمة منسدلة لاختيار قناة موجودة
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

    # الخيار الثاني: إنشاء قناة جديدة عبر زر (منفصل لمنع الأخطاء)
    @discord.ui.button(label="2️⃣ أو إنشاء قناة جديدة ✨", style=discord.ButtonStyle.success, row=1)
    async def create_new_channel(self, interaction: discord.Interaction, button: Button):
        
        # نافذة منبثقة لأخذ اسم القناة
        class NewTicketModal(Modal, title="إنشاء قناة التذاكر"):
            channel_name = TextInput(
                label="اسم القناة (اختياري)",
                placeholder="مثال: 📩・التذاكر",
                required=False
            )
            
            # تمرير الـ View الأب لاستخدام دالة send_ticket_panel
            def __init__(self, parent_view: TicketSetupView):
                super().__init__()
                self.parent_view = parent_view

            async def on_submit(self, modal_inter: discord.Interaction):
                # إذا تركها المستخدم فارغة، نستخدم اسماً مميزاً افتراضياً
                name = self.channel_name.value.strip() or "🎫・التذاكر"

                # إعداد صلاحيات القناة: يرى الأعضاء القناة ولكن لا يمكنهم الكتابة فيها
                overwrites = {
                    modal_inter.guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False, read_message_history=True),
                    modal_inter.guild.me: discord.PermissionOverwrite(send_messages=True, embed_links=True)
                }
                
                # إنشاء القناة
                new_channel = await modal_inter.guild.create_text_channel(name, overwrites=overwrites)
                
                # استدعاء الدالة لإرسال البانر في القناة الجديدة
                await self.parent_view.send_ticket_panel(modal_inter, new_channel)
        
        await interaction.response.send_modal(NewTicketModal(self))
