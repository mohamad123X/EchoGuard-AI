import discord
from discord.ext import commands
from ui_setup import DashboardView
import os

# إعداد البوت مع تفعيل الصلاحيات (Intents) الضرورية
intents = discord.Intents.default()
intents.members = True # ضروري لمعرفة متى يدخل عضو جديد
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# قاعدة بيانات مؤقتة (Dictionary) لحفظ الإعدادات. 
# في المشاريع الكبيرة، يفضل استخدام SQLite أو MongoDB.
bot.db = {} 

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} | System Online 🚀")
    
    # حلقة للمرور على جميع السيرفرات التي يتواجد بها البوت
    for guild in bot.guilds:
        # البحث عن قناة لوحة التحكم
        dashboard_channel = discord.utils.get(guild.channels, name="⚙・لوحة-التحكم")
        
        # إذا لم تكن موجودة، نقوم بإنشائها بصلاحيات صارمة (للإدارة فقط)
        if not dashboard_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            dashboard_channel = await guild.create_text_channel("⚙・لوحة-التحكم", overwrites=overwrites)
            
            # إرسال لوحة التحكم
            embed = discord.Embed(
                title="💠 نظام إدارة السيرفر الآلي",
                description="مرحباً بك في لوحة التحكم المركزية.\nيمكنك من هنا إعداد أنظمة السيرفر بضغطة زر دون الحاجة للأوامر المعقدة.",
                color=discord.Color.from_str("#7000ff") # لون نيون أرجواني
            )
            embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
            
            # عرض الأزرار التفاعلية من ملف ui_setup
            await dashboard_channel.send(embed=embed, view=DashboardView(bot))

bot.run("YOUR_BOT_TOKEN_HERE")
