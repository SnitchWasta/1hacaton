
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup

class DeviceCallbackData(CallbackData, prefix="device"):
    value: str

class DeviceNowCallbackData(CallbackData, prefix="status"):
    value: str

class DateCallbackData(CallbackData, prefix="date"):
    value: str

class SchedulerCallbackData(CallbackData, prefix="scheduler"):
    action: str

class SchedulerStates(StatesGroup):
    waiting_for_schedule = State()

class PeriodState(StatesGroup):
    waiting_for_period = State()