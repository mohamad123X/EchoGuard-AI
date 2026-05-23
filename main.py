import discord
from discord.ext import commands
from ui_setup import DashboardView, TicketPanelView, VerificationPanelView # استدعاء الواجهات

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.db = {}

    # هذه الدالة ضرورية للأزرار الدائمة
    async def setup_hook(self):
        self.add_view(DashboardView(self))
        self.add_view(TicketPanelView())
        
        # بالنسبة لزر التحقق، إذا كان لديك السيرفرات محفوظة في قاعدة بيانات (DB)،
        # نقوم بجلب الرتبة وتمريرها. كحل سريع نمرر None وسيتم استدعاؤها عبر الـ custom_id.
        self.add_view(VerificationPanelView(role_id=0)) # يجب ربط الـ Role ID بقاعدة بياناتك لاحقاً

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | System Online 🚀")
    # (نفس كود إنشاء قناة لوحة التحكم المخفية هنا كما سبق)

bot.run("YOUR_BOT_TOKEN_HERE")
