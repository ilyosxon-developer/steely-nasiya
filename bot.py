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

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()



DB_PATH = "data/nasiya.db"

# data папкасини автоматик яратиш
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
    """ID ларни кетма-кет 1, 2, 3 қилиб тартиблаш"""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT rowid FROM nasiya ORDER BY id")
        rows = cur.fetchall()
        if not rows:
            return
        cur.execute("CREATE TABLE IF NOT EXISTS temp_nasiya AS SELECT * FROM nasiya ORDER BY id")
        cur.execute("DELETE FROM nasiya")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='nasiya'")
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
    if deleted:
        _reorder_ids()
    return deleted


init_db()

@dp.message(Command("start"))
async def start(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🧱 Нержавейка"), types.KeyboardButton(text="🔥 Кўмир")]
        ],
        resize_keyboard=True
    )
    await msg.answer("Салом! Қайси бўлимни кўрмоқчисиз?", reply_markup=keyboard)


@dp.message(lambda m: m.text in ["🧱 Нержавейка", "🔥 Кўмир"])
async def show_nasiya(msg: types.Message):
    tur = "nerjaveyka" if "Нержавейка" in msg.text else "komir"
    items = get_all(tur)
    if not items:
        await msg.answer("Ҳозирча насия маълумотлари йўқ.")
        return
    for i, item in enumerate(items, start=1):
        joy, ism, tel, summa, muddat = item[1:6]
        text = f"📍 {i}. {joy}\n👤 Исм: {ism}\n📞 Телефон: {tel}\n💰 Насия суммаcи: {summa:,} сўм\n📆 Тўлаш муддати: {muddat}"
        await msg.answer(text)


@dp.message(Command("add"))
async def add_data(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("Бу буйруқ фақат админ учун.")
    await msg.answer("Янги насия киритиш учун қуйидаги форматда юборинг:\n\n`жой; исм; тел; сумма; муддат; тур(nerjaveyka/komir)`", parse_mode="Markdown")


@dp.message(lambda m: ";" in m.text)
async def save_data(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    joy, ism, tel, summa, muddat, tur = [x.strip() for x in msg.text.split(";")]
    add_nasiya(joy, ism, tel, int(summa.replace(" ", "")), muddat, tur.lower())
    await msg.answer("✅ Насия сақланди!")


@dp.message(Command("delete"))
async def delete_command(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Бу буйруқ фақат админ учун.")

    try:
        args = msg.text.split()
        if len(args) != 3:
            return await msg.answer("❗ Фойдаланиш: /delete <тур> <id>\nМасалан: /delete nerjaveyka 1")

        tur = args[1].lower()
        nasiya_id = int(args[2])

        if tur not in ["nerjaveyka", "komir"]:
            return await msg.answer("❌ Тур фақат 'nerjaveyka' ёки 'komir' бўлиши мумкин.")

        deleted = delete_one(tur, nasiya_id)
        if deleted:
            await msg.answer(f"✅ {tur} туридаги ID {nasiya_id} насия ўчирилди.")
        else:
            await msg.answer("❌ Бундай ID топилмади.")
    except Exception as e:
        await msg.answer(f"Хатолик юз берди: {e}")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
