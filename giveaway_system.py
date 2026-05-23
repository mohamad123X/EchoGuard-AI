import discord
import random
import asyncio
import re
from discord.ui import View, Button, Modal, TextInput

# دالة ذكية لتحويل المدة الزمنية لنص إلى ثوانٍ (مثال: 10m, 2h, 1d)
def parse_duration(duration_str: str) -> int:
    match = re.match(r"(\d+)([smhd])", duration_str.lower().strip())
    if not match: return 0
    amount, unit = match.groups()
    amount = int(amount)
    if unit == 's': return amount
    if unit == 'm': return amount * 60
    if unit == 'h': return amount * 3600
    if unit == 'd': return amount * 86400
    return 0

class GiveawaySetupView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎯 بدء تهيئة غرف نظام المسابقات", style=discord.ButtonStyle.danger)
    async def deploy_giveaway_channels(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        
        # 1. قناة الإدارة السرية للتحكم بالمسابقات
        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        admin_chan = await guild.create_text_channel("👑・مسابقات-الإدارة", overwrites=admin_overwrites)
        
        # 2. قناة الأعضاء العامة لرؤية السحب
        public_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }
        public_chan = await guild.create_text_channel("🎉・المسابقات-العامة", overwrites=public_overwrites)
        
        # حفظ القنوات في قاعدة بيانات البوت
        g_id = guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['giveaway_admin_channel'] = admin_chan.id
        self.bot.db[g_id]['giveaway_public_channel'] = public_chan.id
        
        # إرسال زر التحكم في القناة الإدارية
        admin_embed = discord.Embed(
            title="👑 لوحة التحكم بالمسابقات | الإدارة فقط",
            description="> اضغط على الزر أدناه لإنشاء جيفاواي وسحب جديد فوراً.\n> سيقوم البوت بفتح نافذة تطلب منك كافة التفاصيل ويرسلها تلقائياً لقناة الأعضاء.",
            color=discord.Color.from_str("#ff0000")
        )
        await admin_chan.send(embed=admin_embed, view=GiveawayStaffView())
        await interaction.response.send_message(f"✅ تم إنشاء القنوات بنجاح!\n- غرفة التحكم: {admin_chan.mention}\n- غرفة الأعضاء: {public_chan.mention}", ephemeral=True)


class GiveawayStaffView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎉 إنشاء مسابقة جديدة (Giveaway)", style=discord.ButtonStyle.primary, custom_id="staff_create_giveaway_btn")
    async def create_giveaway_click(self, interaction: discord.Interaction, button: Button):
        bot = interaction.client
        g_id = interaction.guild.id
        
        # التحقق من إعداد القناة العامة للمسابقات
        public_chan_id = bot.db.get(g_id, {}).get('giveaway_public_channel')
        if not public_chan_id:
            return await interaction.response.send_message("❌ لم يتم تحديد قناة عامة للمسابقات بقاعدة البيانات، يرجى إعادة التهيئة من لوحة التحكم.", ephemeral=True)

        class CreateGiveawayModal(Modal, title="تفاصيل سحب المسابقة"):
            prize = TextInput(label="ما هي الجائزة؟ 🏆", placeholder="مثال: رتبة VIP مجانية / 5000 كريديت", required=True)
            duration = TextInput(label="مدة المسابقة ⏳ (مثال: 10m, 2h, 1d)", placeholder="اكتب المدة بالحروف والارقام...", required=True)
            winners = TextInput(label="عدد الفائزين 👥", default="1", placeholder="اكتب عدد الأشخاص المحظوظين...", required=True)
            req_role = TextInput(label="رتبة إلزامية للمشاركة؟ 🛡️ (اسم الرتبة أو ID)", placeholder="اتركه فارغاً للسماح للجميع...", required=False)
            banner = TextInput(label="رابط صورة للمسابقة 🖼️ (اختياري)", placeholder="ضع رابط الصورة هنا أو اتركه فارغاً لافتراضي فخم...", required=False)

            async def on_submit(self, modal_inter: discord.Interaction):
                seconds = parse_duration(self.duration.value)
                if seconds <= 0:
                    return await modal_inter.response.send_message("❌ صيغة الوقت خاطئة! يرجى استخدام صيغ صحيحة مثل `10m` للمقايق أو `2h` للساعات.", ephemeral=True)
                
                try: num_winners = int(self.winners.value)
                except ValueError: return await modal_inter.response.send_message("❌ يجب أن يكون عدد الفائزين رقماً صحيحاً!", ephemeral=True)
                
                img_url = self.banner.value.strip() or "https://images.unsplash.com/photo-1513151233558-d860c5398176?q=80&w=1000&auto=format&fit=crop"
                
                public_channel = modal_inter.guild.get_channel(public_chan_id)
                if not public_channel:
                    return await modal_inter.response.send_message("❌ تعذر العثور على القناة العامة للمسابقات، ربما تم حذفها!", ephemeral=True)
                
                # إنشاء Embed المسابقة الفخم والملون بالنيون الأحمر للأعضاء
                embed = discord.Embed(
                    title=f"🎉 مسابقة جديدة: {self.prize.value} 🎉",
                    description=(
                        f"> ⏳ **المدّة:** {self.duration.value}\n"
                        f"> 👥 **عدد الفائزين:** {num_winners}\n"
                        f"> 🛡️ **الشرط:** {f'يجب أن تملك رتبة `{self.req_role.value}`' if self.req_role.value else 'مفتوح للجميع! ✅'}\n\n"
                        "اضغط على الزر الأحمر في الأسفل للاشتراك والسحب تلقائياً!"
                    ),
                    color=discord.Color.from_str("#ff0000")
                )
                embed.set_image(url=img_url)
                embed.set_footer(text="تنتهي المسابقة في غضون الوقت المحدد أعلاه ⏳")
                
                await modal_inter.response.send_message("🚀 جاري إرسال وبدء المسابقة في القناة العامة...", ephemeral=True)
                giveaway_msg = await public_channel.send(embed=embed, view=GiveawayJoinView())
                
                # حفظ بيانات المسابقة الحالية في ذاكرة البوت لتتبع المشاركين
                bot.db['active_giveaways'][giveaway_msg.id] = {
                    'entries': [],
                    'prize': self.prize.value,
                    'winners_count': num_winners,
                    'required_role': self.req_role.value if self.req_role.value else None
                }
                
                # بدء مؤقت السحب التلقائي خلف الكواليس
                asyncio.create_task(end_giveaway_task(bot, giveaway_msg, seconds))

        await interaction.response.send_modal(CreateGiveawayModal())


class GiveawayJoinView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎉 انضمام للمسابقة", style=discord.ButtonStyle.danger, custom_id="member_join_giveaway_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: Button):
        bot = interaction.client
        msg_id = interaction.message.id
        
        if msg_id not in bot.db.get('active_giveaways', {}):
            return await interaction.response.send_message("❌ انتهت هذه المسابقة بالفعل أو تم إعادة تشغيل البوت ومسحها!", ephemeral=True)
        
        g_data = bot.db['active_giveaways'][msg_id]
        
        # التحقق من شرط الرتبة إن وجد
        if g_data['required_role']:
            req = g_data['required_role']
            role_obj = discord.utils.get(interaction.guild.roles, name=req) or discord.utils.get(interaction.guild.roles, id=int(req) if req.isdigit() else 0)
            if not role_obj or role_obj not in interaction.user.roles:
                return await interaction.response.send_message(f"❌ لا يمكنك الاشتراك! هذه المسابقة تتطلب رتبة: `{req}`", ephemeral=True)
        
        if interaction.user.id in g_data['entries']:
            return await interaction.response.send_message("أنت مسجل في هذه المسابقة بالفعل! 😎", ephemeral=True)
            
        g_data['entries'].append(interaction.user.id)
        await interaction.response.send_message(f"✅ تم تسجيل دخولك بنجاح للمسابقة على: **{g_data['prize']}**! حظاً موفقاً 🚀", ephemeral=True)

# دالة إنهاء المسابقة واختيار الفائزين بشكل عشوائي ونزيه
async def end_giveaway_task(bot, message: discord.Message, delay: int):
    await asyncio.sleep(delay)
    
    if message.id not in bot.db.get('active_giveaways', {}): return
    g_data = bot.db['active_giveaways'].pop(message.id)
    
    entries = g_data['entries']
    prize = g_data['prize']
    w_count = g_data['winners_count']
    
    if not entries:
        end_embed = discord.Embed(title=f"🛑 انتهت المسابقة: {prize}", description="للاسف لم يشارك أحد في المسابقة، لا يوجد فائزين! 😢", color=discord.Color.dark_gray())
        await message.edit(embed=end_embed, view=None)
        return
        
    # اختيار الفائزين عشوائياً بدون تكرار
    winners_ids = random.sample(entries, k=min(len(entries), w_count))
    winners_mentions = ", ".join([f"<@{w_id}>" for w_id in winners_ids])
    
    end_embed = discord.Embed(
        title=f"🏆 انتهت المسابقة وفزنا بالبطل! 🏆",
        description=f"> 🎉 **الجائزة:** {prize}\n> 👑 **الفائزون:** {winners_mentions}\n\nمبروك لجميع الفائزين وهارد لك للبقية!",
        color=discord.Color.from_str("#00ff00")
    )
    await message.edit(embed=end_embed, view=None)
    await message.channel.send(f"🎉 ألف مبروك {winners_mentions} فوزكم بمسابقة: **{prize}**! تواصلوا مع الإدارة لاستلام جوائزكم.")
