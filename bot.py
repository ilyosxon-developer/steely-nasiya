import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup
import sqlite3
import os

BOT_TOKEN = "8154219948:AAGqF3Bxk0_AqoeE-4HuABFiDVCAwRWGygs"
ADMIN_ID = 5819476520  # O‘zingning Telegram ID


BOT_TOKEN = os.getenv("BOT_TOKEN")  # Tokenni Environment Variable'dan oladi
ADMIN_ID = int(os.getenv("ADMIN_ID"))


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()



DB_PATH = "data/nasiya.db"

# data papkasini avtomatik yaratish
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nasiya (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                joy TEXT,
                ism TEXT,
                tel TEXT,
                summa INTEGER,
                muddat TEXT,
                tur TEXT
            )
        """)
        conn.commit()


def _reorder_ids():
    """ID larni ketma-ket 1, 2, 3 qilib tartiblash"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT rowid FROM nasiya ORDER BY id")
        rows = cur.fetchall()
        if not rows:
            return
        # vaqtincha yangi jadvalga saqlaymiz
        cur.execute("CREATE TABLE IF NOT EXISTS temp_nasiya AS SELECT * FROM nasiya ORDER BY id")
        cur.execute("DELETE FROM nasiya")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='nasiya'")  # AUTOINCREMENT qayta boshlansin
        cur.execute("INSERT INTO nasiya (joy, ism, tel, summa, muddat, tur) SELECT joy, ism, tel, summa, muddat, tur FROM temp_nasiya")
        cur.execute("DROP TABLE temp_nasiya")
        conn.commit()


def add_nasiya(joy, ism, tel, summa, muddat, tur):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO nasiya (joy, ism, tel, summa, muddat, tur)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (joy, ism, tel, summa, muddat, tur))
        conn.commit()


def get_all(tur):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM nasiya WHERE tur=? ORDER BY id", (tur,))
        rows = cur.fetchall()
    return rows


def delete_one(tur, nasiya_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM nasiya WHERE tur=? AND id=?", (tur, nasiya_id))
        deleted = cur.rowcount
        conn.commit()

    # Agar o‘chirilgan bo‘lsa, ID larni qayta tartibla
    if deleted:
        _reorder_ids()

    return deleted


init_db()

@dp.message(Command("start"))
async def start(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🧱 Nerjaveyka"), types.KeyboardButton(text="🔥 Ko‘mir")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Salom! Qaysi bo‘limni ko‘rmoqchisiz?", reply_markup=keyboard)

@dp.message(lambda m: m.text in ["🧱 Nerjaveyka", "🔥 Ko‘mir"])
async def show_nasiya(msg: types.Message):
    tur = "nerjaveyka" if "Nerjaveyka" in msg.text else "komir"
    items = get_all(tur)
    if not items:
        await msg.answer("Hozircha nasiya ma’lumotlari yo‘q.")
        return
    for i, item in enumerate(items, start=1):
        joy, ism, tel, summa, muddat = item[1:6]
        text = f"📍 {i}. {joy}\n👤 Ism: {ism}\n📞 Telefon: {tel}\n💰 Nasiya summasi: {summa:,} so‘m\n📆 To‘lash muddati: {muddat}"
        await msg.answer(text)

@dp.message(Command("add"))
async def add_data(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("Bu buyruq faqat admin uchun.")
    await msg.answer("Yangi nasiya kiritish uchun quyidagi formatda yuboring:\n\n`joy; ism; tel; summa; muddat; tur(nerjaveyka/komir)`", parse_mode="Markdown")

@dp.message(lambda m: ";" in m.text)
async def save_data(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    joy, ism, tel, summa, muddat, tur = [x.strip() for x in msg.text.split(";")]
    add_nasiya(joy, ism, tel, int(summa.replace(" ", "")), muddat, tur.lower())
    await msg.answer("✅ Nasiya saqlandi!")

@dp.message(Command("delete"))
async def delete_command(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Bu buyruq faqat admin uchun.")

    try:
        # xabar: /delete nerjaveyka 1
        args = msg.text.split()
        if len(args) != 3:
            return await msg.answer("❗ Foydalanish: /delete <tur> <id>\nMasalan: /delete nerjaveyka 1")

        tur = args[1].lower()
        nasiya_id = int(args[2])

        if tur not in ["nerjaveyka", "komir"]:
            return await msg.answer("❌ Tur faqat 'nerjaveyka' yoki 'komir' bo‘lishi mumkin.")

        deleted = delete_one(tur, nasiya_id)
        if deleted:
            await msg.answer(f"✅ {tur} turidagi ID {nasiya_id} nasiya o‘chirildi.")
        else:
            await msg.answer("❌ Bunday ID topilmadi.")
    except Exception as e:
        await msg.answer(f"Xatolik yuz berdi: {e}")



async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
