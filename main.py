import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

# استيراد الواجهات لضمان ديمومتها عبر إعادة التشغيل
from ui_setup import DashboardView, VerificationPanelView, WelcomeSetupView
from ticket_system import TicketPanelView
from giveaway_system import GiveawayStaffView, GiveawayJoinView

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        
        # قاعدة البيانات المؤقتة الهيكلية
        self.db = {
            'active_giveaways': {} # لحفظ المسابقات النشطة ومعرفات الرسائل الخاصه بها
        }

    async def setup_hook(self):
        # تسجيل الأزرار الدائمة لتعمل 24/7
        self.add_view(DashboardView(self))
        self.add_view(TicketPanelView())
        self.add_view(VerificationPanelView())
        self.add_view(WelcomeSetupView(self))
        self.add_view(GiveawayStaffView())
        self.add_view(GiveawayJoinView())
        
        # تحميل ملف الأحداث المشترك (الترحيب، اللوج، الرد التلقائي، الرتبة التلقائية)
        try:
            await self.load_extension("events_handler")
            print("✅ تم تحميل نظام الأحداث المتكامل بنجاح.")
        except Exception as e:
            print(f"❌ خطأ في تحميل نظام الأحداث: {e}")
            
        await self.tree.sync()
        print("✅ تم مزامنة جميع أوامر السلاش بنجاح.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | Sentinel Ultra Core Online 🚀")
    
    # إنشاء لوحة التحكم التلقائية عند التشغيل
    for guild in bot.guilds:
        dashboard_channel = discord.utils.get(guild.text_channels, name="⚙・لوحة-التحكم")
        if not dashboard_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            dashboard_channel = await guild.create_text_channel("⚙・لوحة-التحكم", overwrites=overwrites)
        
        await dashboard_channel.purge(limit=5)
        
        embed = discord.Embed(
            title="💠 مركز التحكم الرئيسي الخارق | Sentinel HQ",
            description=(
                "> **مرحباً بك في لوحة الإدارة الذكية الجيل الجديد.**\n\n"
                "اضغط على الأزرار أدناه لإعداد وتفعيل أنظمة السيرفر فوراً وبشكل منسق."
            ),
            color=discord.Color.from_str("#00f2ff")
        )
        embed.set_image(url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop")
        embed.set_footer(text="Sentinel Management System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await dashboard_channel.send(embed=embed, view=DashboardView(bot))

@bot.tree.command(name="panel", description="إظهار لوحة تحكم البوت للإدارة")
@discord.app_commands.default_permissions(administrator=True) 
async def show_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💠 مركز التحكم الرئيسي",
        description="> يرجى اختيار النظام المراد إعداده من الأسفل:",
        color=discord.Color.from_str("#00f2ff")
    )
    await interaction.response.send_message(embed=embed, view=DashboardView(bot), ephemeral=True)

token = os.getenv("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في البيئة!")
