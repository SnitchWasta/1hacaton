from info import TOKEN
import sqlite3 
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio 
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from functions import get_info, process_all, write_info_in, dates_command, names_command

bot = Bot(token=TOKEN)
dp = Dispatcher()

connect = sqlite3.connect("database.db") 
command = connect.cursor

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот на aiogram.")

@dp.message(Command("info"))
async def send_info(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Всю информацию"),
            types.KeyboardButton(text="Конкретное устройство"),
            types.KeyboardButton(text="По дате")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите тип желаемой информации"
    )
    await message.answer("Какую информацию предоставить?", reply_markup=keyboard)

@dp.message(F.text.lower() == "всю информацию")
async def all_info(message: types.Message):
    write_info_in(process_all())
    await message.answer_document(FSInputFile('otchet.txt'))

class DeviceCallbackData(CallbackData, prefix="device"):
    value: str

class DateCallbackData(CallbackData, prefix="date"):
    value: str

@dp.message(F.text.lower() == "конкретное устройство")
async def choose_equip(message: types.Message):
    builder = InlineKeyboardBuilder()
    names = command.execute(names_command).fetchall()
    
    for name in names:
        device_name = str(name[0])
        builder.add(types.InlineKeyboardButton(
            text=device_name.encode('windows-1251').decode('utf-8'),
            callback_data=DeviceCallbackData(value=device_name).pack()
        ))
    
    await message.answer(
        "Выберите устройство:",
        reply_markup=builder.as_markup()
    )

@dp.message(F.text.lower() == "по дате")
async def choose_date(message: types.Message):
    builder = InlineKeyboardBuilder()
    dates = command.execute(dates_command).fetchall()
    
    for date in dates:
        date_period = str(date[0])
        builder.add(types.InlineKeyboardButton(
            text=date_period,
            callback_data=DateCallbackData(value=date_period).pack()
        ))
    
    await message.answer(
        "Выберите дату:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(DateCallbackData.filter())
async def Datecallback(
    callback: types.CallbackQuery, 
    callback_data: DateCallbackData
):
    date_value = callback_data.value
    names = command.execute(names_command).fetchall()
    info = ""
    for name in names:
        info += get_info(name[0], date_value)
    write_info_in(info)
    await callback.message.answer_document(FSInputFile('otchet.txt'))

@dp.callback_query(DeviceCallbackData.filter())
async def Devicecallback(
    callback: types.CallbackQuery, 
    callback_data: DeviceCallbackData
):
    device_value = callback_data.value
    dates = command.execute(dates_command).fetchall()
    info = ""
    for date in dates:
        info += get_info(device_value, date[0])
    write_info_in(info)
    await callback.message.answer_document(FSInputFile('otchet.txt'))

async def start_bot():
    await dp.start_polling(bot)

asyncio.run(start_bot())

######## перекодировка #########
#name = name.encode('utf-8').decode('windows-1251')
    