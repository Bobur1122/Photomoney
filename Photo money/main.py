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
import os

ADMINS = list(map(int, os.getenv("ADMINS").split(',')))

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS



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
    return user_id == ADMIN_ID

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 👤 USER HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
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
    await callback.message.answer(f"Xo'sh, endi rasmni yuboring, shunda men sizga narxini ayta olaman ♻️")
    await state.set_state(UserFlow.waiting_photo)

@user_router.message(UserFlow.waiting_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    
    processing_msg = await message.answer("Rasmni ko'ryapman, kutib turing...⏳")
    
    photo_file_id = message.photo[-1].file_id
    if user_id not in BotConfig.user_sessions:
        BotConfig.user_sessions[user_id] = {}
    BotConfig.user_sessions[user_id]['photo_file_id'] = photo_file_id

    # 40-70 sekund kutish
    wait_time = random.randint(40, 70)
    # Testing uchun: wait_time = random.randint(4, 6)
    
    await state.set_state(UserFlow.waiting_price)
    
    # Countdown
    start_time = asyncio.get_event_loop().time()
    last_update = 0
    
    while True:
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        remaining = wait_time - elapsed
        
        if remaining <= 0:
            break
        
        # Har 30 soniyada yangilash
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
    
    # Narxni hisoblash
    price = random.randint(100000, 250000)
    price_formatted = f"{price:,}".replace(",", " ")
    
    if user_id not in BotConfig.user_sessions:
        BotConfig.user_sessions[user_id] = {}
    BotConfig.user_sessions[user_id]['price'] = price
    
    # Natija rasimini yubor
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
        
        try:
            await bot.send_message(ADMIN_ID, admin_notification)
        except:
            pass

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
        
        try:
            await bot.send_message(ADMIN_ID, admin_notification)
        except:
            pass
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

@admin_router.callback_query(F.data == "admin_edit_start")
async def admin_edit_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.answer(
        "✏️ Yangi start xabarini yuboring:\n\n"
        "ℹ️ {first_name} - foydalanuvchi ismi o'rniga avtomatik qo'yiladi\n\n"
        "Bekor qilish: /cancel"
    )
    await state.set_state(AdminStates.editing_start_message)

@admin_router.message(AdminStates.editing_start_message)
async def save_start_message(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("❌ Bekor qilindi")
        await state.clear()
        return
    
    BotConfig.start_message = message.text
    await message.answer("✅ Start xabari o'zgartirildi!")
    await state.clear()

@admin_router.callback_query(F.data == "admin_add_start_image")
async def admin_add_start_image(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.answer(
        "🖼️ Start bo'sh joyida ko'rinadi bo'lgan rasmni yuboring:\n\n"
        "Bekor qilish: /cancel"
    )
    await state.set_state(AdminStates.adding_start_image)

@admin_router.message(AdminStates.adding_start_image, F.photo)
async def save_start_image(message: Message, state: FSMContext):
    BotConfig.start_image_file_id = message.photo[-1].file_id
    await message.answer("✅ Start rasmi saqlandi!")
    await state.clear()

@admin_router.message(AdminStates.adding_start_image)
async def wrong_start_image(message: Message):
    await message.answer("❌ Faqat rasm yuborish mumkin!")

@admin_router.callback_query(F.data == "admin_add_result_image")
async def admin_add_result_image(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.answer(
        f"🖼️ Natija bo'yida ko'rinadi bo'lgan rasmni yuboring:\n\n"
        f"Mavjud rasmlar: {len(BotConfig.result_images)} ta\n\n"
        "Bekor qilish: /cancel"
    )
    await state.set_state(AdminStates.adding_result_image)

@admin_router.message(AdminStates.adding_result_image, F.photo)
async def save_result_image(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    BotConfig.result_images.append(file_id)
    await message.answer(f"✅ Rasm saqlandi!\nJami: {len(BotConfig.result_images)} ta")
    await state.clear()

@admin_router.message(AdminStates.adding_result_image)
async def wrong_result_image(message: Message):
    await message.answer("❌ Faqat rasm yuborish mumkin!")

@admin_router.callback_query(F.data == "admin_add_channel")
async def admin_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.answer(
        "📢 Kanal qo'shish - 1/3 qadam\n\n"
        "Kanal ID sini yuboring:\n\n"
        "🔹 @kanal_nomi\n"
        "🔹 -100123456789\n\n"
        "Bekor qilish: /cancel"
    )
    await state.set_state(AdminStates.adding_channel_id)

@admin_router.message(AdminStates.adding_channel_id)
async def save_channel_id(message: Message, state: FSMContext, bot: Bot):
    if message.text == "/cancel":
        await message.answer("❌ Bekor qilindi")
        await state.clear()
        return
    
    channel_input = message.text.strip()
    
    try:
        if channel_input.startswith("@"):
            chat = await bot.get_chat(channel_input)
            chat_id = chat.id
        elif channel_input.startswith("-100"):
            chat_id = int(channel_input)
        else:
            await message.answer("❌ Format noto'g'ri!")
            return
        
        await state.update_data(chat_id=chat_id)
        
        await message.answer(
            "✅ ID qabul qilindi!\n\n"
            "📢 Kanal qo'shish - 2/3 qadam\n\n"
            "Invite linkini yuboring:\n\nBekor qilish: /cancel"
        )
        await state.set_state(AdminStates.adding_channel_link)
        
    except Exception as e:
        await message.answer(f"❌ Xato: {str(e)}")

@admin_router.message(AdminStates.adding_channel_link)
async def save_channel_link(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("❌ Bekor qilindi")
        await state.clear()
        return
    
    invite_link = message.text.strip()
    
    if "t.me/" not in invite_link:
        await message.answer("❌ To'g'ri Telegram link kiriting!")
        return
    
    await state.update_data(invite_link=invite_link)
    
    await message.answer(
        "✅ Link qabul qilindi!\n\n"
        "📢 Kanal qo'shish - 3/3 qadam\n\n"
        "Kanal nomini yuboring:\n\nBekor qilish: /cancel"
    )
    await state.set_state(AdminStates.adding_channel_name)

@admin_router.message(AdminStates.adding_channel_name)
async def save_channel_name(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("❌ Bekor qilindi")
        await state.clear()
        return
    
    name = message.text.strip()
    data = await state.get_data()
    chat_id = data.get('chat_id')
    invite_link = data.get('invite_link')
    
    BotConfig.required_channels.append((chat_id, invite_link, name))
    
    await message.answer(
        f"✅ Kanal qo'shildi!\n\n"
        f"📢 {name}\n"
        f"🆔 {chat_id}\n\n"
        f"Jami: {len(BotConfig.required_channels)} ta"
    )
    await state.clear()

@admin_router.callback_query(F.data == "admin_list_channels")
async def admin_list_channels(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await callback.answer()
    
    if not BotConfig.required_channels:
        await callback.message.answer("📋 Kanallar bo'sh")
        return
    
    buttons = []
    for idx, (chat_id, invite_link, name) in enumerate(BotConfig.required_channels):
        buttons.append([InlineKeyboardButton(text=f"❌ {name}", callback_data=f"delete_channel_{idx}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")])
    
    channels_text = "📋 Kanallar:\n\n"
    for idx, (chat_id, invite_link, name) in enumerate(BotConfig.required_channels, 1):
        channels_text += f"{idx}. {name}\n"
    
    await callback.message.answer(channels_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@admin_router.callback_query(F.data.startswith("delete_channel_"))
async def delete_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    idx = int(callback.data.split("_")[2])
    if 0 <= idx < len(BotConfig.required_channels):
        deleted = BotConfig.required_channels.pop(idx)
        await callback.answer(f"✅ {deleted[2]} o'chirildi!")
        await admin_list_channels(callback)

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🛠 Admin Panel",
        reply_markup=get_admin_panel_keyboard()
    )

@admin_router.callback_query(F.data == "admin_view_settings")
async def admin_view_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    channels_info = f"{len(BotConfig.required_channels)} ta" if BotConfig.required_channels else "Bo'sh"
    result_images_info = f"{len(BotConfig.result_images)} ta" if BotConfig.result_images else "Bo'sh"
    start_image_status = '✅ Mavjud' if BotConfig.start_image_file_id else '❌ Yoq'
    active_users = len(BotConfig.user_sessions)
    start_msg = BotConfig.start_message[:100]
    
    settings_text = f"""⚙️ Joriy sozlamalar:

📝 Start xabari:
{start_msg}...

🖼️ Start rasmi: {start_image_status}

🖼️ Natija rasmlari: {result_images_info}

📢 Kanallar: {channels_info}

👥 Aktiv foydalanuvchilar: {active_users}"""
    
    await callback.answer()
    await callback.message.answer(settings_text)

@admin_router.message(Command("cancel"))
async def cancel_admin_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    await message.answer("❌ Bekor qilindi")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    """Initialize and start bot"""
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
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"📢 Kanallar: {len(BotConfig.required_channels)} ta")
    print("━" * 50)
    
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

