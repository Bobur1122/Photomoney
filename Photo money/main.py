"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 PROFESSIONAL TELEGRAM BOT v2.1 - COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Features: Start rasmi, Admin rasm-qo'shish, 4-6 min kutish, Habar qolishi
"""

import asyncio
import random
import logging
from typing import Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))  # .env: ADMINS=123456,987654321

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 GLOBAL STORAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BotConfig:
    """Runtime memory storage"""
    start_message = "Salom, {first_name}! 👋\n\nMen Photo moto robot\n\nFotosuratlaringizni yuklang — va shu yerning o'zida to'lov oling.\nQanchalik ko'p foto yuborsangiz, shunchalik foyda va bonuslar olasiz! 🚀\n\nAgar siz tayor busayiz,\nDavom etish tugmasini bosing 🏆"
    
    start_image_file_id = None
    result_images = []
    required_channels = []
    user_sessions = {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📝 FSM STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserFlow(StatesGroup):
    waiting_phone_type = State()
    waiting_photo = State()
    waiting_price = State()

class AdminStates(StatesGroup):
    editing_start_message = State()
    adding_start_image = State()
    adding_result_image = State()
    adding_channel_id = State()
    adding_channel_link = State()
    adding_channel_name = State()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 KEYBOARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_continue_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Davom etish", callback_data="continue")]
    ])

def get_phone_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 iPhone", callback_data="phone_iphone")],
        [InlineKeyboardButton(text="🤖 Android", callback_data="phone_android")]
    ])

def get_withdraw_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Pul yechib olish", callback_data="withdraw")]
    ])

def get_subscription_keyboard(unsubscribed_channels):
    buttons = []
    for invite_link, name in unsubscribed_channels:
        buttons.append([InlineKeyboardButton(text=f"📢 {name}", url=invite_link)])
    buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Start xabarini o'zgartirish", callback_data="admin_edit_start")],
        [InlineKeyboardButton(text="🖼️ Start rasimini qo'shish", callback_data="admin_add_start_image")],
        [InlineKeyboardButton(text="🖼️ Natija rasmini qo'shish", callback_data="admin_add_result_image")],
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
        [InlineKeyboardButton(text="⚙️ Sozlamalarni ko'rish", callback_data="admin_view_settings")]
    ])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_subscription(bot: Bot, user_id: int):
    if not BotConfig.required_channels:
        return True, []
    
    unsubscribed = []
    for channel_data in BotConfig.required_channels:
        chat_id, invite_link, name = channel_data
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in [
                ChatMemberStatus.MEMBER, 
                ChatMemberStatus.ADMINISTRATOR, 
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.RESTRICTED
            ]:
                unsubscribed.append((invite_link, name))
        except Exception as e:
            logging.error(f"Subscription check error for {name}: {e}")
            unsubscribed.append((invite_link, name))
    
    return len(unsubscribed) == 0, unsubscribed

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

async def notify_admins(bot: Bot, text: str):
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logging.error(f"Admin ga xabar jo'natishda xato: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👤 USER HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    await state.clear()
    BotConfig.user_sessions[user_id] = {}
    
    welcome_text = BotConfig.start_message.format(first_name=first_name)
    
    if BotConfig.start_image_file_id:
        try:
            await message.answer_photo(
                photo=BotConfig.start_image_file_id,
                caption=welcome_text,
                reply_markup=get_continue_keyboard()
            )
        except Exception as e:
            logging.error(f"Photo send error: {e}")
            await message.answer(welcome_text, reply_markup=get_continue_keyboard())
    else:
        await message.answer(welcome_text, reply_markup=get_continue_keyboard())

@user_router.callback_query(F.data == "continue")
async def process_continue(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Telefoningiz modelini tanlang?",
        reply_markup=get_phone_type_keyboard()
    )
    await state.set_state(UserFlow.waiting_phone_type)

@user_router.callback_query(F.data.startswith("phone_"))
async def process_phone_type(callback: CallbackQuery, state: FSMContext):
    phone_type = "iPhone" if callback.data == "phone_iphone" else "Android"
    
    user_id = callback.from_user.id
    if user_id not in BotConfig.user_sessions:
        BotConfig.user_sessions[user_id] = {}
    BotConfig.user_sessions[user_id]['phone_type'] = phone_type
    
    await callback.answer()
    await callback.message.answer("Xo'sh, endi rasmni yuboring, shunda men sizga narxini ayta olaman ♻️")
    await state.set_state(UserFlow.waiting_photo)

@user_router.message(UserFlow.waiting_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    processing_msg = await message.answer("Rasmni ko'ryapman, kutib turing...⏳")
    
    photo_file_id = message.photo[-1].file_id
    if user_id not in BotConfig.user_sessions:
        BotConfig.user_sessions[user_id] = {}
    BotConfig.user_sessions[user_id]['photo_file_id'] = photo_file_id

    wait_time = random.randint(40, 70)
    await state.set_state(UserFlow.waiting_price)
    
    start_time = asyncio.get_event_loop().time()
    last_update = 0
    
    while True:
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        remaining = wait_time - elapsed
        if remaining <= 0:
            break
        if remaining % 30 == 0 and remaining != last_update:
            last_update = remaining
            minutes = remaining // 60
            seconds = remaining % 60
            try:
                await processing_msg.edit_text(
                    f"Rasm tekshirilmoqda... ⏳\n\n"
                    f"Qolgan vaqt: {minutes}:{seconds:02d}"
                )
            except:
                pass
        await asyncio.sleep(1)
    
    price = random.randint(100000, 250000)
    price_formatted = f"{price:,}".replace(",", " ")
    
    if user_id not in BotConfig.user_sessions:
        BotConfig.user_sessions[user_id] = {}
    BotConfig.user_sessions[user_id]['price'] = price
    
    result_text = f"""Tabriklayman! 🎉 Rasmning 
💰 Narxi: {price_formatted} so'm"""
    
    if BotConfig.result_images:
        random_image = random.choice(BotConfig.result_images)
        try:
            await processing_msg.delete()
            await message.answer_photo(
                photo=random_image,
                caption=result_text,
                reply_markup=get_withdraw_keyboard()
            )
        except:
            try:
                await processing_msg.edit_text(result_text)
            except:
                await processing_msg.delete()
                await message.answer(result_text, reply_markup=get_withdraw_keyboard())
    else:
        try:
            await processing_msg.delete()
        except:
            pass
        await message.answer(result_text, reply_markup=get_withdraw_keyboard())
    
    await state.clear()

@user_router.message(UserFlow.waiting_photo)
async def wrong_media_type(message: Message):
    await message.answer("Faqat rasm yuborish mumkin ❌")

@user_router.callback_query(F.data == "withdraw")
async def process_withdraw(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed, unsubscribed = await check_subscription(bot, user_id)
    
    if not is_subscribed:
        await callback.answer()
        await callback.message.answer(
            "Quyidagi kanallar(ga) obuna bo'ling:\n\nPul yechish uchun avval barcha kanallarga obuna bo'lishingiz kerak ❗",
            reply_markup=get_subscription_keyboard(unsubscribed)
        )
    else:
        await callback.answer("✅ So'rov qabul qilindi!")
        await callback.message.answer(
            "So'rovingiz qabul qilindi ✅\n1–3 kun ichida siz bilan bog'lanamiz."
        )
        
        user_info = callback.from_user
        price = BotConfig.user_sessions.get(user_id, {}).get('price', 0)
        price_formatted = f"{price:,}".replace(",", " ")
        username = user_info.username or "yoq"
        
        admin_notification = f"""🔔 Yangi pul yechish so'rovi

👤 Foydalanuvchi: {user_info.first_name}
🆔 ID: {user_id}
💰 Summa: {price_formatted} so'm
📱 Username: @{username}
⏰ Vaqt: {datetime.now().strftime('%H:%M:%S')}"""
        
        await notify_admins(bot, admin_notification)

@user_router.callback_query(F.data == "check_subscription")
async def recheck_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed, unsubscribed = await check_subscription(bot, user_id)
    
    if is_subscribed:
        await callback.answer("✅ Siz barcha kanallarga obuna bo'lgansiz!")
        await callback.message.answer(
            "So'rovingiz qabul qilindi ✅\n1–3 kun ichida siz bilan bog'lanamiz."
        )
        
        user_info = callback.from_user
        price = BotConfig.user_sessions.get(user_id, {}).get('price', 0)
        price_formatted = f"{price:,}".replace(",", " ")
        username = user_info.username or "yoq"
        
        admin_notification = f"""🔔 Yangi pul yechish so'rovi

👤 Foydalanuvchi: {user_info.first_name}
🆔 ID: {user_id}
💰 Summa: {price_formatted} so'm
📱 Username: @{username}
⏰ Vaqt: {datetime.now().strftime('%H:%M:%S')}"""
        
        await notify_admins(bot, admin_notification)
    else:
        missing_channels = ", ".join([name for _, name in unsubscribed])
        await callback.answer(f"❌ Siz hali obuna bo'lmagansiz: {missing_channels}", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👨‍💼 ADMIN HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

admin_router = Router()

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q!")
        return
    
    await message.answer(
        "🛠 Admin Panel\n\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_panel_keyboard()
    )

# ... qolgan admin handlerlar asl kodingizdagidek ishlaydi, faqat ADMIN_ID o'rniga notify_admins va is_admin ishlatiladi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(admin_router)
    dp.include_router(user_router)
    
    print("━" * 50)
    print("🤖 Bot ishga tushdi!")
    print(f"👤 Adminlar: {ADMINS}")
    print(f"📢 Kanallar: {len(BotConfig.required_channels)} ta")
    print("━" * 50)
    
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
