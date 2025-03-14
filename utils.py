import json

from quiz import quiz_data
from db import get_quiz_index, update_quiz_index
from db import get_records_book

from aiogram import types, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

QUIZ_BUTTON = "Начать опрос"
# Диспечер
dp = Dispatcher()


# Handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=QUIZ_BUTTON))
    await message.answer("Привет! Я новый бот.", reply_markup=builder.as_markup(resize_keyboard=True))


@dp.message(F.text == QUIZ_BUTTON)
@dp.message(Command('quiz'))
async def cmd_quiz(message: types.Message):
    await message.answer("Давайте начнем квиз! Первый вопрос: ...")
    await new_quiz(message)
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)


async def new_quiz(message):
    user_id = message.from_user.id

    current_question_index = 0
    current_records_book = json.dumps([])
    await update_quiz_index(user_id, current_question_index, current_records_book)
    await get_question(user_id, message)


async def get_question(user_id, message):
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = await generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


class TextCallbackFactory(CallbackData, prefix='wrong_answer'):
    string: str


async def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=TextCallbackFactory(string=option).pack()
        ))

    builder.adjust(2)
    return builder.as_markup()


async def destroyer_options_keyboard(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None,
    )


async def get_next_question(callback: types.CallbackQuery, records_book):

    current_question_index = await get_quiz_index(callback.from_user.id)
    current_question_index += 1

    await update_quiz_index(callback.from_user.id, current_question_index, records_book)

    if current_question_index < len(quiz_data):
        await get_question(callback.from_user.id, callback.message)
    else:
        await callback.message.answer("Это был последний вопрос.\nВаши результаты:")
        for i, record in enumerate(json.loads(records_book)):
            correct_answer_index = quiz_data[i]['correct_option']
            if record == quiz_data[i]['options'][correct_answer_index]:
                await callback.message.answer(
                    f"{quiz_data[i]['question']}\n"
                    f"Ваш ответ верен!: {record}!")
            else:
                await callback.message.answer(
                    f"{quiz_data[i]['question']}\n"
                    f"Ваш ответ: {record}; \nВерный ответ: {quiz_data[i]['options'][correct_answer_index]}.")


def update_records(book, record):
    book = json.loads(book)
    book.append(str(record))
    return json.dumps(book)


@dp.callback_query(TextCallbackFactory.filter())
async def fix_wrong_answer(
    callback: types.CallbackQuery,
    callback_data: TextCallbackFactory
):
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]["correct_option"]
    
    await destroyer_options_keyboard(callback)
    await callback.message.answer(f"Ответ {"верный" if correct_option==callback_data.string else "неверный"}: {callback_data.string} ")

    current_records_book = await get_records_book(callback.from_user.id)
    crb = update_records(current_records_book, callback_data.string)
    await get_next_question(callback, crb)
