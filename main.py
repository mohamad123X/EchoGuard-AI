import discord
import os
from discord.ext import commands
from ui_setup import DashboardView
from ticket_system import TicketPanelView

class MyBot(commands.Bot):
    def __init__(self):
        # تفعيل الـ Intents الضرورية
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        
        # قاعدة بيانات مؤقتة (ملاحظة: تُمسح عند إعادة التشغيل، يُفضل لاحقاً ربطها بـ SQLite)
        self.db = {}

    async def setup_hook(self):
        # تسجيل الأزرار الدائمة لتعمل دائماً
        self.add_view(DashboardView(self))
        self.add_view(TicketPanelView())
        
        # تحميل ملف الترحيب (لم يكن يعمل في الكود السابق)
        try:
            await self.load_extension("welcome_event")
            print("✅ تم تحميل نظام الترحيب.")
        except Exception as e:
            print(f"❌ خطأ في تحميل الترحيب: {e}")
            
        # مزامنة أوامر السلاش
        await self.tree.sync()
        print("✅ تم مزامنة أوامر السلاش بنجاح.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | Sentinel System Online 🚀")
    
    for guild in bot.guilds:
        dashboard_channel = discord.utils.get(guild.text_channels, name="⚙・لوحة-التحكم")
        
        if not dashboard_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            dashboard_channel = await guild.create_text_channel("⚙・لوحة-التحكم", overwrites=overwrites)
        
        await dashboard_channel.purge(limit=10)
        
        embed = discord.Embed(
            title="💠 مركز التحكم الرئيسي | Sentinel",
            description="> **مرحباً بك في لوحة الإدارة الذكية.**\n> اختر النظام الذي تريد إعداده من الأزرار أدناه لبناء هيكل السيرفر الخاص بك بأسرع وقت.",
            color=discord.Color.from_str("#00f2ff")
        )
        embed.set_footer(text="Sentinel Admin Panel", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await dashboard_channel.send(embed=embed, view=DashboardView(bot))

@bot.tree.command(name="panel", description="إظهار لوحة تحكم البوت (للإدارة فقط)")
@discord.app_commands.default_permissions(administrator=True) 
async def show_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💠 مركز التحكم الرئيسي",
        description="> **مرحباً بك في لوحة الإدارة الذكية.**\n> يرجى اختيار النظام المراد إعداده:",
        color=discord.Color.from_str("#00f2ff")
    )
    await interaction.response.send_message(embed=embed, view=DashboardView(bot), ephemeral=True)

token = os.getenv("DISCORD_TOKEN")
if token is None:
    print("❌ خطأ: لم يتم العثور على التوكن! تأكد من ملف .env أو المتغيرات.")
else:
    bot.run(token)
