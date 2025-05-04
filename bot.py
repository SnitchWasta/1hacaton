from info import TOKEN
import sqlite3 
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio 
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from functions import get_info, process_all, write_info_in, dates_command, names_command
from classes import DateCallbackData, DeviceCallbackData, SchedulerCallbackData, SchedulerStates, DeviceNowCallbackData
from aiogram.fsm.context import FSMContext
from analize import start_cycle, check_end_of_cycle, check_start_of_cycle, get_range_info, get_current_info
schedule_token = False
schedule_interval = 10


bot = Bot(token=TOKEN)
dp = Dispatcher()


# connect = sqlite3.connect("database.db") 
# command = connect.cursor()


async def task_run(id):
    global schedule_token, schedule_interval
    while True:
        if schedule_token:
            await send_report(id)
            await asyncio.sleep(schedule_interval * 60) 


@dp.message(Command("start"))
async def start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Настроить планировщик"),
            types.KeyboardButton(text="Получить состояние устройства"),
            #types.KeyboardButton(text="Состояние устройства за последний период")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите опцию"
    )
    await message.answer("Выберите опцию", reply_markup=keyboard)



@dp.message(F.text.lower() == "получить состояние устройства")
async def get_device_info(message: types.Message):
    builder = InlineKeyboardBuilder()
    connect = sqlite3.connect("database.db") 
    command = connect.cursor()
    names = command.execute(names_command)
    
    for name in names:
        builder.add(
            types.InlineKeyboardButton(
                text = f"{name[0]}",
                callback_data=DeviceNowCallbackData(value = name[0]).pack()
            )
        )
    connect.close()
    await message.answer(
        "Выберите устройство",
        reply_markup=builder.as_markup()
    )


def remake_array(x):
    print(x)
    string = ""
    for i in x:
        string += str(i) + " | "
    return string + "\n"


@dp.callback_query(DeviceNowCallbackData.filter())
async def handle_scheduler_callback(
    callback: types.CallbackQuery, 
    callback_data: DeviceNowCallbackData
):
    name = callback_data.value
    write_info_in(remake_array(get_current_info(name)))
    await callback.message.answer_document(FSInputFile('otchet.txt'))



@dp.message(F.text.lower() == "настроить планировщик")
async def scheduler_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    global schedule_interval, schedule_token

    print(f"Текущее состояние schedule_token: {schedule_token}")
    
    if schedule_token:
        builder.add(types.InlineKeyboardButton(
            text="Выключить",
            callback_data=SchedulerCallbackData(action="disable").pack(),
        ))
    else:
        builder.add(types.InlineKeyboardButton(
            text="Включить",
            callback_data=SchedulerCallbackData(action="enable").pack(),
        ))
    
    builder.add(types.InlineKeyboardButton(
        text="Настроить интервал",
        callback_data=SchedulerCallbackData(action="set").pack(),
    ))
    now_settings = f"Текущие настройки планировщика:\n{'Включен' if schedule_token else 'Выключен'}\nИнтервал: {schedule_interval} (мин)"
    await message.answer(
        now_settings,
        reply_markup=builder.as_markup()
    )


@dp.callback_query(SchedulerCallbackData.filter())
async def handle_scheduler_callback(
    callback: types.CallbackQuery, 
    callback_data: SchedulerCallbackData,
    state: FSMContext
):
    global schedule_token, schedule_interval 
    action = callback_data.action
    print(f"Обработка действия: {action}")
    
    if action == "disable":
        schedule_token = False
        print(f"Расписание отключено. Текущий статус: {schedule_token}")
        await callback.answer("Расписание отключено")
    elif action == "enable":
        schedule_token = True
        print(f"Расписание включено. Текущий статус: {schedule_token}")
        asyncio.create_task(task_run(callback.message.chat.id))
        await callback.answer("Расписание включено")
    elif action == "set":
        await callback.answer()
        await callback.message.answer("Пожалуйста, введите новое расписание в формате ЧЧ:ММ")
        await state.set_state(SchedulerStates.waiting_for_schedule)
    
    await state.update_data(schedule_token=schedule_token)


@dp.message(SchedulerStates.waiting_for_schedule)
async def process_schedule_input(message: types.Message, state: FSMContext):
    global schedule_interval
    user_input = message.text
    if not validate_time_format(user_input):
        await message.answer("Неверный формат времени. Пожалуйста, используйте ЧЧ:ММ")
        return
    
    await state.update_data(schedule_time=user_input)
    data = await state.get_data()
    
    apply_new_schedule(user_input)

    await message.answer(f"Новое расписание установлено: {user_input}")
    await state.clear()


def validate_time_format(time_str: str) -> bool:
    try:
        hours, minutes = map(int, time_str.split(':'))
        return 0 <= hours < 24 and 0 <= minutes < 60
    except ValueError:
        return False


def apply_new_schedule(time_str: str):
    global schedule_interval
    hours, minutes = map(int, time_str.split(':'))
    schedule_interval = hours * 60 + minutes
    print(f"Установлено новое время: {time_str}")


def get_halfhour_report():
    info_str = ""
    connect = sqlite3.connect("database.db") 
    command = connect.cursor()
    names = command.execute(names_command)
    for name in names:
        print(name)
        check_start_of_cycle(name[0])
        info_str += remake_array(get_current_info(name[0]))
        check_end_of_cycle(name[0])
    connect.close()
    print(info_str)
    write_info_in(info_str)


async def send_report(chat_id: int):
    get_halfhour_report()
    await bot.send_document(chat_id=chat_id, document=FSInputFile('otchet.txt'))


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


@dp.message(F.text.lower() == "конкретное устройство")
async def choose_equip(message: types.Message):
    builder = InlineKeyboardBuilder()
    connect = sqlite3.connect("database.db") 
    command = connect.cursor()

    names = command.execute(names_command).fetchall()
    connect.close()
    for name in names:
        device_name = str(name[0])
        builder.add(types.InlineKeyboardButton(
            text=device_name,
            callback_data=DeviceCallbackData(value=device_name).pack()
        ))
    
    await message.answer(
        "Выберите устройство:",
        reply_markup=builder.as_markup()
    )


@dp.message(F.text.lower() == "по дате")
async def choose_date(message: types.Message):
    builder = InlineKeyboardBuilder()
    connect = sqlite3.connect("database.db") 
    command = connect.cursor()
    dates = command.execute(dates_command).fetchall()
    connect.close()
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
    connect = sqlite3.connect("database.db") 
    command = connect.cursor()
    names = command.execute(names_command).fetchall()
    connect.close()
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
    connect = sqlite3.connect("database.db") 
    command = connect.cursor()
    dates = command.execute(dates_command).fetchall()
    connect.close()
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
    