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
        
        category = await guild.create_category("🎉 قسم المسابقات")
        
        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        admin_chan = await guild.create_text_channel("👑・مسابقات-الإدارة", category=category, overwrites=admin_overwrites)
        
        public_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
        }
        public_chan = await guild.create_text_channel("🎉・المسابقات-العامة", category=category, overwrites=public_overwrites)
        
        g_id = guild.id
        if g_id not in self.bot.db: self.bot.db[g_id] = {}
        self.bot.db[g_id]['giveaway_admin_channel'] = admin_chan.id
        self.bot.db[g_id]['giveaway_public_channel'] = public_chan.id
        
        admin_embed = discord.Embed(
            title="👑 لوحة التحكم بالمسابقات | الإدارة فقط",
            description="> اضغط على الزر أدناه لإنشاء مسابقة.\n> سيقوم البوت بفتح نافذة تطلب التفاصيل، وينشئ **قناة مراقبة حية** تظهر لك المشتركين.",
            color=discord.Color.from_str("#ff0000")
        )
        await admin_chan.send(embed=admin_embed, view=GiveawayStaffView())
        await interaction.response.send_message("✅ تم إنشاء قسم وغرف المسابقات بنجاح!", ephemeral=True)


class GiveawayStaffView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎉 إنشاء مسابقة جديدة", style=discord.ButtonStyle.primary, custom_id="staff_create_giveaway_btn")
    async def create_giveaway_click(self, interaction: discord.Interaction, button: Button):
        bot = interaction.client
        g_id = interaction.guild.id
        
        public_chan_id = bot.db.get(g_id, {}).get('giveaway_public_channel')
        if not public_chan_id:
            return await interaction.response.send_message("❌ لم يتم تحديد قناة عامة للمسابقات.", ephemeral=True)

        class CreateGiveawayModal(Modal, title="تفاصيل المسابقة"):
            prize = TextInput(label="الجائزة 🏆", placeholder="مثال: رتبة VIP", required=True)
            duration = TextInput(label="المدة ⏳", placeholder="مثال: 10m, 2h", required=True)
            winners = TextInput(label="عدد الفائزين 👥", default="1", required=True)
            req_role = TextInput(label="رتبة إلزامية؟ (اختياري)", required=False)
            banner = TextInput(label="رابط صورة للمسابقة (اختياري)", required=False)

            async def on_submit(self, modal_inter: discord.Interaction):
                seconds = parse_duration(self.duration.value)
                if seconds <= 0: return await modal_inter.response.send_message("❌ صيغة الوقت خاطئة!", ephemeral=True)
                
                try: num_winners = int(self.winners.value)
                except ValueError: return await modal_inter.response.send_message("❌ عدد الفائزين يجب أن يكون رقماً!", ephemeral=True)
                
                role_req_str = self.req_role.value.strip()
                role_mention = "مفتوح للجميع! ✅"
                role_id_to_save = None

                if role_req_str:
                    role_obj = discord.utils.get(modal_inter.guild.roles, name=role_req_str)
                    if not role_obj and role_req_str.isdigit(): role_obj = modal_inter.guild.get_role(int(role_req_str))
                    if role_obj:
                        role_mention = f"يجب أن تملك رتبة {role_obj.mention}"
                        role_id_to_save = role_obj.id

                img_url = self.banner.value.strip() or "https://i.postimg.cc/ZnmfxDPk/download.jpg"
                public_channel = modal_inter.guild.get_channel(public_chan_id)
                
                embed = discord.Embed(
                    title=f"🎉 مسابقة: {self.prize.value} 🎉",
                    description=f"> ⏳ **المدّة:** {self.duration.value}\n> 👥 **الفائزين:** {num_winners}\n> 🛡️ **الشرط:** {role_mention}\n\nاضغط للاشتراك!",
                    color=discord.Color.red()
                )
                embed.set_image(url=img_url)
                
                await modal_inter.response.send_message("🚀 جاري بدء المسابقة وإنشاء غرفة المراقبة...", ephemeral=True)
                giveaway_msg = await public_channel.send(embed=embed, view=GiveawayJoinView())
                
                # --- إنشاء غرفة مراقبة المسابقة للإدارة ---
                admin_chan = discord.utils.get(modal_inter.guild.channels, name="👑・مسابقات-الإدارة")
                cat = admin_chan.category if admin_chan else None
                tracker_chan = await modal_inter.guild.create_text_channel(
                    name=f"مراقبة-{self.prize.value[:10]}", 
                    category=cat,
                    overwrites={
                        modal_inter.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        modal_inter.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                )
                
                tracker_embed = discord.Embed(
                    title="📊 مراقبة المشتركين الحية",
                    description="**الأعضاء المشتركون (0):**\nلا يوجد أحد بعد.",
                    color=discord.Color.blue()
                )
                tracker_msg = await tracker_chan.send(embed=tracker_embed)
                
                bot.db['active_giveaways'][giveaway_msg.id] = {
                    'entries': [],
                    'prize': self.prize.value,
                    'winners_count': num_winners,
                    'required_role': role_id_to_save,
                    'tracker_channel_id': tracker_chan.id,
                    'tracker_msg_id': tracker_msg.id
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
        
        if g_data['required_role']:
            role_obj = interaction.guild.get_role(g_data['required_role'])
            if not role_obj or role_obj not in interaction.user.roles:
                return await interaction.response.send_message(f"❌ لا يمكنك الاشتراك! يتطلب رتبة: {role_obj.mention if role_obj else 'محذوفة'}", ephemeral=True)
        
        if interaction.user.id in g_data['entries']:
            return await interaction.response.send_message("أنت مسجل بالفعل! 😎", ephemeral=True)
            
        g_data['entries'].append(interaction.user.id)
        await interaction.response.send_message("✅ تم تسجيل دخولك بنجاح! حظاً موفقاً 🚀", ephemeral=True)
        
        # --- تحديث قائمة المشتركين الحية للإدارة ---
        tracker_chan = interaction.guild.get_channel(g_data.get('tracker_channel_id'))
        if tracker_chan:
            try:
                tracker_msg = await tracker_chan.fetch_message(g_data.get('tracker_msg_id'))
                total = len(g_data['entries'])
                
                # عرض آخر 40 مشترك كحد أقصى لتجنب تخطي حد حروف ديسكورد
                display_entries = g_data['entries'][-40:] 
                mentions = [f"<@{uid}>" for uid in display_entries]
                desc = f"**الأعضاء المشتركون ({total}):**\n" + ", ".join(mentions)
                if total > 40: desc += f"\n... و {total - 40} آخرين."
                
                embed = tracker_msg.embeds[0]
                embed.description = desc
                await tracker_msg.edit(embed=embed)
            except: pass

async def end_giveaway_task(bot, message: discord.Message, delay: int):
    await asyncio.sleep(delay)
    if message.id not in bot.db.get('active_giveaways', {}): return
    g_data = bot.db['active_giveaways'].pop(message.id)
    
    entries = g_data['entries']
    
    # حذف قناة المراقبة بعد انتهاء المسابقة لتنظيف السيرفر
    tracker_chan = message.guild.get_channel(g_data.get('tracker_channel_id'))
    if tracker_chan: 
        try: await tracker_chan.delete(reason="انتهت المسابقة")
        except: pass

    if not entries:
        await message.edit(embed=discord.Embed(title="🛑 انتهت المسابقة", description="لم يشارك أحد!", color=discord.Color.dark_gray()), view=None)
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
