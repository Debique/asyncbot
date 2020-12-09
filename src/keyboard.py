from aiogram.types import reply_keyboard, inline_keyboard

main_menu =  reply_keyboard.ReplyKeyboardMarkup([['Полное совпадение', 'Частичное совпадение']], resize_keyboard=True)

back_button = reply_keyboard.ReplyKeyboardMarkup([['Назад']], resize_keyboard=True)
