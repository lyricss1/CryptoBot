import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiohttp
import time


TOKEN = os.getenv("TOKEN")

TOKEN = "TOKEN_BOT"

#coin
COINS = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "TON": "Toncoin",
    "BNB": "BNB",
    "DOGE": "Dogecoin",
    "XRP": "Ripple",
    "ADA": "Cardano"
}

PRICE_CACHE = {}
CACHE_TTL = 8

dp = Dispatcher()
session: aiohttp.ClientSession | None = None

#api
async def fetch_price(symbol: str):
    now = time.time()
    cached = PRICE_CACHE.get(symbol)
    if cached and now - cached[1] < CACHE_TTL:
        return cached[0]

    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    async with session.get(url) as r:
        if r.status != 200:
            return None
        data = await r.json()
        price = float(data["price"])
        PRICE_CACHE[symbol] = (price, now)
        return price
#btn
def coins_keyboard():
    rows, row = [], []
    for s, n in COINS.items():
        row.append(InlineKeyboardButton(text=f"{n} ({s})", callback_data=f"coin:{s}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)
def coin_keyboard(symbol: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Refresh", callback_data=f"coin:{symbol}")],
        [InlineKeyboardButton(text="Back", callback_data="menu")]
    ])

@dp.message(Command("start"))
@dp.message(Command("coins"))
async def show_menu(msg: types.Message):
    await msg.answer(
        "<b>Crypto Prices</b>\nChoose a coin below",
        reply_markup=coins_keyboard(),
        parse_mode="HTML"
    )



@dp.callback_query(F.data == "menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text(
        "<b>Crypto Prices</b>\nChoose a coin below",
        reply_markup=coins_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("coin:"))
async def on_coin_click(call: CallbackQuery):
    symbol = call.data.split(":")[1]
    price = await fetch_price(symbol)
    if price is None:
        await call.answer("Failed to fetch price", show_alert=True)
        return

    if price > 1000:
        view = f"{price:,.0f}"
    elif price > 1:
        view = f"{price:,.2f}"
    else:
        view = f"{price:.6f}"
    title = COINS.get(symbol, symbol)
    text = (
        f"<b>{title} ({symbol})</b>\n"
        f"────────────\n"
        f"Price: <b>${view}</b> USDT"
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=coin_keyboard(symbol),
            parse_mode="HTML"
        )
    except:
        await call.answer()


async def main():
    global session
    logging.basicConfig(level=logging.INFO)
    session = aiohttp.ClientSession()
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await session.close()


if __name__ == "__main__":
    asyncio.run(main())