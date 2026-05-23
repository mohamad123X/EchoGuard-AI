import discord
import os
from discord.ext import commands
from ui_setup import DashboardView, TicketPanelView, VerificationPanelView 

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.db = {}

    # هذه الدالة ضرورية للأزرار الدائمة لتعمل بعد إعادة تشغيل البوت
    async def setup_hook(self):
        self.add_view(DashboardView(self))
        self.add_view(TicketPanelView())
        self.add_view(VerificationPanelView(role_id=0))

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | Sentinel System Online 🚀")
    
    # المرور على جميع السيرفرات التي يتواجد فيها البوت
    for guild in bot.guilds:
        # البحث عن قناة لوحة التحكم
        dashboard_channel = discord.utils.get(guild.text_channels, name="⚙・لوحة-التحكم")
        
        # إذا لم تكن القناة موجودة، نقوم بإنشائها بصلاحيات للإدارة فقط (مخفية عن الأعضاء)
        if not dashboard_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            dashboard_channel = await guild.create_text_channel("⚙・لوحة-التحكم", overwrites=overwrites)
        
        # تنظيف القناة من الرسائل القديمة (لتجنب تراكم الأزرار)
        await dashboard_channel.purge(limit=10)
        
        # إرسال لوحة التحكم الرئيسية بتصميم نيون احترافي
        embed = discord.Embed(
            title="💠 مركز التحكم الرئيسي",
            description="مرحباً بك في لوحة الإدارة الذكية.\nاختر النظام الذي تريد إعداده من الأزرار أدناه لبناء هيكل السيرفر الخاص بك:",
            color=discord.Color.from_str("#00f2ff")
        )
        await dashboard_channel.send(embed=embed, view=DashboardView(bot))


# ==========================================
# سحب التوكن من المتغيرات (Variables) في Railway وتشغيل البوت
# ==========================================
token = os.getenv("DISCORD_TOKEN")

if token is None:
    print("❌ خطأ: لم يتم العثور على التوكن! تأكد من إضافة DISCORD_TOKEN في إعدادات المنصة.")
else:
    bot.run(token)
