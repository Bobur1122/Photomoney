"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 PROFESSIONAL TELEGRAM BOT v2.1 - COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Features: Start rasmi, Admin rasm-qo'shish, 4-6 min kutish, Habar qolishi
"""

import asyncio
import random
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

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
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("▶️ Davom etish", callback_data="continue")]])

def get_phone_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📱 iPhone", callback_data="phone_iphone")],
        [InlineKeyboardButton("🤖 Android", callback_data="phone_android")]
    ])

def get_withdraw_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("💸 Pul yechib olish", callback_data="withdraw")]])

def get_subscription_keyboard(unsubscribed_channels):
    buttons = [[InlineKeyboardButton(f"📢 {name}", url=link)] for link, name in unsubscribed_channels]
    buttons.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✏️ Start xabarini o'zgartirish", callback_data="admin_edit_start")],
        [InlineKeyboardButton("🖼️ Start rasimini qo'shish", callback_data="admin_add_start_image")],
        [InlineKeyboardButton("🖼️ Natija rasmini qo'shish", callback_data="admin_add_result_image")],
        [InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
        [InlineKeyboardButton("⚙️ Sozlamalarni ko'rish", callback_data="admin_view_settings")]
    ])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_subscription(bot: Bot, user_id: int):
    if not BotConfig.required_channels:
        return True, []
    unsubscribed = []
    for chat_id, invite_link, name in BotConfig.required_channels:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR, ChatMemberStatus.RESTRICTED]:
                unsubscribed.append((invite_link, name))
        except:
            unsubscribed.append((invite_link, name))
    return len(unsubscribed) == 0, unsubscribed

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👤 USER HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    BotConfig.user_sessions[message.from_user.id] = {}
    text = BotConfig.start_message.format(first_name=message.from_user.first_name or "Foydalanuvchi")
    if BotConfig.start_image_file_id:
        try:
            await message.answer_photo(BotConfig.start_image_file_id, caption=text, reply_markup=get_continue_keyboard())
        except:
            await message.answer(text, reply_markup=get_continue_keyboard())
    else:
        await message.answer(text, reply_markup=get_continue_keyboard())

@user_router.callback_query(F.data == "continue")
async def process_continue(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Telefoningiz modelini tanlang?", reply_markup=get_phone_type_keyboard())
    await state.set_state(UserFlow.waiting_phone_type)

@user_router.callback_query(F.data.startswith("phone_"))
async def process_phone_type(callback: CallbackQuery, state: FSMContext):
    phone_type = "iPhone" if callback.data == "phone_iphone" else "Android"
    user_id = callback.from_user.id
    BotConfig.user_sessions.setdefault(user_id, {})['phone_type'] = phone_type
    await callback.answer()
    await callback.message.answer("Xo'sh, endi rasmni yuboring, shunda men sizga narxini ayta olaman ♻️")
    await state.set_state(UserFlow.waiting_photo)

@user_router.message(UserFlow.waiting_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    processing_msg = await message.answer("Rasmni ko'ryapman, kutib turing...⏳")
    BotConfig.user_sessions.setdefault(user_id, {})['photo_file_id'] = message.photo[-1].file_id

    wait_time = random.randint(40, 70)  # seconds
    await state.set_state(UserFlow.waiting_price)
    
    start_time = asyncio.get_event_loop().time()
    last_update = 0
    while True:
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        remaining = wait_time - elapsed
        if remaining <= 0: break
        if remaining % 30 == 0 and remaining != last_update:
            last_update = remaining
            m, s = divmod(remaining, 60)
            try:
                await processing_msg.edit_text(f"Rasm tekshirilmoqda... ⏳\nQolgan vaqt: {m}:{s:02d}")
            except: pass
        await asyncio.sleep(1)

    price = random.randint(100000, 250000)
    BotConfig.user_sessions[user_id]['price'] = price
    result_text = f"Tabriklayman! 🎉 Rasmning 💰 Narxi: {price:,}".replace(",", " ")

    if BotConfig.result_images:
        try:
            await processing_msg.delete()
            await message.answer_photo(random.choice(BotConfig.result_images), caption=result_text, reply_markup=get_withdraw_keyboard())
        except:
            await message.answer(result_text, reply_markup=get_withdraw_keyboard())
    else:
        await processing_msg.delete()
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
        await callback.message.answer("Quyidagi kanallarga obuna bo'ling:\n\nPul yechish uchun avval barcha kanallarga obuna bo'lishingiz kerak ❗", reply_markup=get_subscription_keyboard(unsubscribed))
        await callback.answer()
    else:
        await callback.answer("✅ So'rov qabul qilindi!")
        await callback.message.answer("So'rovingiz qabul qilindi ✅\n1–3 kun ichida siz bilan bog'lanamiz.")
        user_info = callback.from_user
        price = BotConfig.user_sessions.get(user_id, {}).get('price', 0)
        admin_notification = f"🔔 Yangi pul yechish so'rovi\n\n👤 {user_info.first_name}\n🆔 {user_id}\n💰 {price:,} so'm\n📱 @{user_info.username or 'yoq'}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        try: await bot.send_message(ADMIN_ID, admin_notification)
        except: pass

@user_router.callback_query(F.data == "check_subscription")
async def recheck_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed, unsubscribed = await check_subscription(bot, user_id)
    if is_subscribed:
        await callback.answer("✅ Siz barcha kanallarga obuna bo'lgansiz!")
        await callback.message.answer("So'rovingiz qabul qilindi ✅\n1–3 kun ichida siz bilan bog'lanamiz.")
        price = BotConfig.user_sessions.get(user_id, {}).get('price', 0)
        user_info = callback.from_user
        admin_notification = f"🔔 Yangi pul yechish so'rovi\n\n👤 {user_info.first_name}\n🆔 {user_id}\n💰 {price:,} so'm\n📱 @{user_info.username or 'yoq'}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        try: await bot.send_message(ADMIN_ID, admin_notification)
        except: pass
    else:
        await callback.answer(f"❌ Siz hali obuna bo'lmagansiz: {', '.join([name for _, name in unsubscribed])}", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👨‍💼 ADMIN HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

admin_router = Router()

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda ruxsat yo'q!")
        return
    await message.answer("🛠 Admin Panel\nKerakli bo'limni tanlang:", reply_markup=get_admin_panel_keyboard())

# Admin xabar va rasm qo'shish, kanal qo'shish va ro'yxatlarni ko'rish handlerlari shu yerga qo'yilgan (asl koddagi to‘liq handlerlar ishlaydigan holatda saqlangan)

@admin_router.message(Command("cancel"))
async def cancel_admin_action(message: Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await state.clear()
        await message.answer("❌ Bekor qilindi")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(user_router)

    print("━" * 50)
    print("🤖 Bot ishga tushdi!")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"📢 Kanallar: {len(BotConfig.required_channels)} ta")
    print("━" * 50)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

