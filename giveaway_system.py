import discord
import random
import asyncio
import re
from discord.ui import View, Button, Modal, TextInput

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
        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        admin_chan = await guild.create_text_channel("👑・مسابقات-الإدارة", overwrites=admin_overwrites)
        
        public_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }
        public_chan = await guild.create_text_channel("🎉・المسابقات-العامة", overwrites=public_overwrites)
        
        g_id = guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['giveaway_admin_channel'] = admin_chan.id
        self.bot.db[g_id]['giveaway_public_channel'] = public_chan.id
        
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
        
        public_chan_id = bot.db.get(g_id, {}).get('giveaway_public_channel')
        if not public_chan_id:
            return await interaction.response.send_message("❌ لم يتم تحديد قناة عامة للمسابقات بقاعدة البيانات.", ephemeral=True)

        class CreateGiveawayModal(Modal, title="تفاصيل سحب المسابقة"):
            prize = TextInput(label="ما هي الجائزة؟ 🏆", placeholder="مثال: رتبة VIP / 5000 كريديت", required=True)
            duration = TextInput(label="مدة المسابقة ⏳ (مثال: 10m, 2h, 1d)", required=True)
            winners = TextInput(label="عدد الفائزين 👥", default="1", required=True)
            req_role = TextInput(label="رتبة إلزامية للمشاركة؟ 🛡️ (الـ ID أو الاسم)", required=False)
            banner = TextInput(label="رابط صورة للمسابقة 🖼️ (اختياري)", required=False)

            async def on_submit(self, modal_inter: discord.Interaction):
                seconds = parse_duration(self.duration.value)
                if seconds <= 0:
                    return await modal_inter.response.send_message("❌ صيغة الوقت خاطئة!", ephemeral=True)
                
                try: num_winners = int(self.winners.value)
                except ValueError: return await modal_inter.response.send_message("❌ عدد الفائزين يجب أن يكون رقماً!", ephemeral=True)
                
                # جلب الرتبة لطباعة اسمها بدلاً من الأيدي الخاص بها (الإصلاح)
                role_req_str = self.req_role.value.strip()
                role_mention = "مفتوح للجميع! ✅"
                role_id_to_save = None

                if role_req_str:
                    # محاولة البحث بالاسم
                    role_obj = discord.utils.get(modal_inter.guild.roles, name=role_req_str)
                    # إذا لم يجد بالاسم، وكان المدخل أرقاماً، نبحث بالـ ID
                    if not role_obj and role_req_str.isdigit():
                        role_obj = modal_inter.guild.get_role(int(role_req_str))
                    
                    if role_obj:
                        role_mention = f"يجب أن تملك رتبة {role_obj.mention}"
                        role_id_to_save = role_obj.id
                    else:
                        return await modal_inter.response.send_message("❌ لم أتمكن من العثور على الرتبة المحددة. تأكد من الاسم أو الـ ID.", ephemeral=True)

                # صورة المسابقات الافتراضية
                img_url = self.banner.value.strip() or "https://i.postimg.cc/ZnmfxDPk/download.jpg"
                
                public_channel = modal_inter.guild.get_channel(public_chan_id)
                if not public_channel:
                    return await modal_inter.response.send_message("❌ تعذر العثور على القناة العامة للمسابقات!", ephemeral=True)
                
                embed = discord.Embed(
                    title=f"🎉 مسابقة جديدة: {self.prize.value} 🎉",
                    description=(
                        f"> ⏳ **المدّة:** {self.duration.value}\n"
                        f"> 👥 **عدد الفائزين:** {num_winners}\n"
                        f"> 🛡️ **الشرط:** {role_mention}\n\n"
                        "اضغط على الزر الأحمر في الأسفل للاشتراك والسحب تلقائياً!"
                    ),
                    color=discord.Color.from_str("#ff0000")
                )
                embed.set_image(url=img_url)
                embed.set_footer(text="تنتهي المسابقة في غضون الوقت المحدد أعلاه ⏳")
                
                await modal_inter.response.send_message("🚀 جاري إرسال وبدء المسابقة...", ephemeral=True)
                giveaway_msg = await public_channel.send(embed=embed, view=GiveawayJoinView())
                
                bot.db['active_giveaways'][giveaway_msg.id] = {
                    'entries': [],
                    'prize': self.prize.value,
                    'winners_count': num_winners,
                    'required_role': role_id_to_save
                }
                
                asyncio.create_task(end_giveaway_task(bot, giveaway_msg, seconds))

        await interaction.response.send_modal(CreateGiveawayModal())


class GiveawayJoinView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎉 انضمام للمسابقة", style=discord.ButtonStyle.danger, custom_id="member_join_giveaway_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: Button):
        bot = interaction.client
        msg_id = interaction.message.id
        
        if msg_id not in bot.db.get('active_giveaways', {}):
            return await interaction.response.send_message("❌ انتهت هذه المسابقة!", ephemeral=True)
        
        g_data = bot.db['active_giveaways'][msg_id]
        
        # التحقق من الرتبة بالأيدي المحفوظ
        if g_data['required_role']:
            role_obj = interaction.guild.get_role(g_data['required_role'])
            if not role_obj or role_obj not in interaction.user.roles:
                return await interaction.response.send_message(f"❌ لا يمكنك الاشتراك! يجب أن تمتلك رتبة: {role_obj.mention if role_obj else 'محذوفة'}", ephemeral=True)
        
        if interaction.user.id in g_data['entries']:
            return await interaction.response.send_message("أنت مسجل في هذه المسابقة بالفعل! 😎", ephemeral=True)
            
        g_data['entries'].append(interaction.user.id)
        await interaction.response.send_message(f"✅ تم تسجيل دخولك بنجاح! حظاً موفقاً 🚀", ephemeral=True)

async def end_giveaway_task(bot, message: discord.Message, delay: int):
    await asyncio.sleep(delay)
    if message.id not in bot.db.get('active_giveaways', {}): return
    g_data = bot.db['active_giveaways'].pop(message.id)
    
    entries = g_data['entries']
    if not entries:
        end_embed = discord.Embed(title="🛑 انتهت المسابقة", description="لم يشارك أحد!", color=discord.Color.dark_gray())
        await message.edit(embed=end_embed, view=None)
        return
        
    winners_ids = random.sample(entries, k=min(len(entries), g_data['winners_count']))
    winners_mentions = ", ".join([f"<@{w_id}>" for w_id in winners_ids])
    
    end_embed = discord.Embed(
        title=f"🏆 انتهت المسابقة وفزنا بالبطل! 🏆",
        description=f"> 🎉 **الجائزة:** {g_data['prize']}\n> 👑 **الفائزون:** {winners_mentions}",
        color=discord.Color.from_str("#00ff00")
    )
    await message.edit(embed=end_embed, view=None)
    await message.channel.send(f"🎉 ألف مبروك {winners_mentions} فوزكم بمسابقة: **{g_data['prize']}**!")
