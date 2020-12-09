import datetime
import time

from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from aiogram import types
from bs4 import BeautifulSoup
import asyncio
import aiohttp

from src.config import TOKEN
from src.states import ArticleFinder
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import src.keyboard as kb

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
loop = asyncio.get_event_loop()


@dp.message_handler(lambda msg: msg.text == 'Назад', state="*")
async def back(msg):
    tel_id = msg.chat.id
    await bot.send_message(tel_id, "Выберите критерий поиска.", reply_markup=kb.main_menu)


@dp.message_handler(commands=['start'], state="*")
async def start(message):
    tel_id = message.chat.id
    await bot.send_message(tel_id, "Здравствуйте! \nВыберите критерий поиска.", reply_markup=kb.main_menu)


@dp.message_handler(lambda msg: msg.text == 'Частичное совпадение', state="*")
async def partly_search(msg):
    tel_id = msg.chat.id
    await bot.send_message(tel_id, 'Введите артикуль товара.', reply_markup=kb.back_button)
    await ArticleFinder.waiting_partly_search.set()


@dp.message_handler(lambda msg: msg.text == 'Полное совпадение', state="*")
async def partly_search(msg):
    tel_id = msg.chat.id
    await bot.send_message(tel_id, 'Введите артикуль товара.', reply_markup=kb.back_button)
    await ArticleFinder.waiting_full_search.set()


@dp.message_handler(content_types=['text'], state=ArticleFinder.waiting_partly_search)
async def enteredText(message: types.message):
    await bot.send_message(message.chat.id, "⏳Секунду, ищу товар...⏳\n")
    await bot.send_message(message.chat.id, "<b>zipm.ru</b>\n", parse_mode="HTML")
    await zipm(message.text, message.chat.id)
    await part33(message.text, message.chat.id)
    await arlos(message.text, message.chat.id)
    await ArticleFinder.main_menu.set()
    await back(message)


@dp.message_handler(content_types=['text'], state=ArticleFinder.waiting_full_search)
async def enteredText(message: types.message):
    await bot.send_message(message.chat.id, "⏳Секунду, ищу товар...⏳\n")
    await zipm_fully(message.text, message.chat.id)
    await part33_fully(message.text, message.chat.id)
    await arlos_fully(message.text, message.chat.id)
    await ArticleFinder.main_menu.set()
    await back(message)


async def get_html(url):
    timeout = aiohttp.ClientTimeout(total=40)
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers={'User-Agent': ua},
                                     timeout=timeout) as session:
        async with session.request('get', url) as responce:
            return await responce.content.read()


async def zipm(art, tel_id):
    print('ZIPM start', datetime.datetime.now())
    alreadyPrinted = 0
    divided = False
    firstly = True
    main_url = 'https://zipm.ru/'
    html = await get_html(f'https://zipm.ru/catalog/?search={art}&onlycode=0&job=search')
    bs = BeautifulSoup(html, 'lxml')
    products = bs.find_all('div', {'class': 'col-12 col-sm-6 col-md-6 col-lg-6 col-xl-3'})
    text = ""
    final = ""
    counter = len(products)
    first_message = None
    first_message_text = ""
    if len(products) == 0:
        text += f'<b>zipm.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        print('ZIPM end', datetime.datetime.now())
        return
    for product in products:
        if alreadyPrinted == 8:
            divided = True
            if firstly:
                final = f'<b>zipm.ru</b>\n\n'
                final += f"Найдено результатов: {counter}\n\n"
                firstly = False
            final += text
            alreadyPrinted = 0
            first_message_text = text
            text = ""
            first_message = await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')
            final = ""
        alreadyPrinted+=1
        cardTitle = product.find('div', {'class': 'card-title'})
        name = cardTitle.text
        link = f"{main_url}{cardTitle.find('a').get('href')}"
        product_name = f'<a href="{link}">{name}</a>'
        exist = product.find('span', {'class': 'blockpkz'})
        if exist is None:
            exist = "В наличии"
        elif exist.text == "Не поставляется":
            counter-=1
            if counter == 0:
                text += f'<b>zipm.ru</b>\n\n'
                text += "❌Товара не найдено❌"
                await bot.send_message(tel_id, text, parse_mode='HTML')
                print('ZIPM end', datetime.datetime.now())
                return
            continue
        else:
            exist = exist.text
        price = product.find('span', {'class': 'price'})
        if price is None:
            price = "По запросу"
        else:
            price = price.text
        text += f'💸Цена: {price}\n'
        text += f'✅{exist}\n'
        text += f'{product_name}\n\n'
    if divided is False:
        final = f'<b>zipm.ru</b>\n\n'
        final += f"Найдено результатов: {counter}\n\n"
    final += text
    await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')
    if divided:
        final = f'<b>zipm.ru</b>\n\n'
        final += f"Найдено результатов: {counter}\n\n"
        final += first_message_text
        try:
            await bot.edit_message_text(final, tel_id, first_message.message_id, parse_mode='HTML', disable_web_page_preview=True)
        except Exception:
            print('MessageNotModified')
    print('ZIPM end', datetime.datetime.now())


async def zipm_fully(art, tel_id):
    main_url = 'https://zipm.ru/'
    html = await get_html(f'https://zipm.ru/catalog/?search={art}&onlycode=0&job=search')
    bs = BeautifulSoup(html, 'lxml')
    products = bs.find_all('div', {'class': 'col-12 col-sm-6 col-md-6 col-lg-6 col-xl-3'})
    text = ""
    counter = 0
    if len(products) == 0:
        text += f'<b>zipm.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    for product in products:
        article = product.find('div', {'class': 'mini'}).text.split(':')[1].strip()
        if art == article:
            counter += 1
            cardTitle = product.find('div', {'class': 'card-title'})
            name = cardTitle.text
            link = f"{main_url}{cardTitle.find('a').get('href')}"
            product_name = f'<a href="{link}">{name}</a>'
            exist = product.find('span', {'class': 'blockpkz'})
            if exist is None:
                exist = "В наличии"
            elif exist.text == "Не поставляется":
                text += f'<b>zipm.ru</b>\n\n'
                text += "❌Товара не найдено❌"
                await bot.send_message(tel_id, text, parse_mode='HTML')
                return
            else:
                exist = exist.text
            price = product.find('span', {'class': 'price'})
            if price is None:
                price = "По запросу"
            else:
                price = price.text
            text += f'💸Цена: {price}\n'
            text += f'✅{exist}\n'
            text += f'{product_name}\n\n'
    if counter == 0:
        text += f'<b>zipm.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    final = f'<b>zipm.ru</b>\n\n'
    final += text
    await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')


async def part33(art, tel_id):
    print('PART33 start', datetime.datetime.now())
    main_url = 'https://www.part33.ru/'
    html = await get_html(f'https://www.part33.ru/catalog/search/?query={art}')
    bs = BeautifulSoup(html, 'lxml')
    products = bs.find_all('div', {'class': 'card-box'})
    text = ""
    final = ""
    counter = len(products)
    first_message = None
    first_message_text = ""
    alreadyPrinted = 0
    firstly = True
    divided = False
    if len(products) == 0:
        text += f'<b>part33.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        print('PART33 end', datetime.datetime.now())
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    for product in products:
        if alreadyPrinted == 8:
            divided = True
            if firstly:
                final = f'<b>part33.ru</b>\n\n'
                final += f"Найдено результатов: {counter}\n\n"
                firstly = False
            final += text
            alreadyPrinted = 0
            first_message_text = text
            text = ""
            #first_message = await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')
            final = ""
        alreadyPrinted+=1
        link = f"{product.find('a').get('href')}"
        name = product.find('a', {'class': 'card-title'}).text.strip()
        product_name = f'<a href="{link}">{name}</a>'
        exist = product.find('div', {'class': 'card-total'}).text
        exist = exist.replace('\n', '').strip()
        if exist == "Нет в наличии":
            counter-=1
            if counter == 0:
                text += f'<b>part33.ru</b>\n\n'
                text += "❌Товара не найдено❌"
                await bot.send_message(tel_id, text, parse_mode='HTML')
                print('PART33 end', datetime.datetime.now())
                return
            continue
        price = product.find('div', {'class': 'card-price'}).text.replace('\n', '').strip()
        text += f'💵Цена: {price}\n'
        text += f'✅{exist}\n'
        text += f'{product_name}\n\n'
    if divided is False:
        final = f'<b>part33.ru</b>\n\n'
        final += f"Найдено результатов: {counter}\n\n"
        final += text
        #await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')
    if divided:
        final = f'<b>part33.ru</b>\n\n'
        final += f"Найдено результатов: {counter}\n\n"
        final += first_message_text
        try:
            await bot.edit_message_text(final, tel_id, first_message.message_id, parse_mode='HTML', disable_web_page_preview=True)
        except Exception:
            print('MessageNotModified')
    print('PART33 end', datetime.datetime.now())


async def part33_fully(art, tel_id):
    main_url = 'https://www.part33.ru/'
    html = await get_html(f'https://www.part33.ru/catalog/search/?query={art}')
    bs = BeautifulSoup(html, 'lxml')
    products = bs.find_all('div', {'class': 'card-box'})
    text = ""
    if len(products) == 0:
        text += f'<b>part33.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    counter = 0
    for product in products:
        article = product.find('a', {'class': 'card-title'}).text.strip().split(' ')[0].strip()
        print(article)
        if art == article:
            counter += 1
            link = f"{product.find('a').get('href')}"
            name = product.find('a', {'class': 'card-title'}).text.strip()
            product_name = f'<a href="{link}">{name}</a>'
            exist = product.find('div', {'class': 'card-total'}).text
            exist = exist.replace('\n', '').strip()
            if exist == "Нет в наличии":
                text += f'<b>part33.ru</b>\n\n'
                text += "❌Товара не найдено❌"
                #await bot.send_message(tel_id, text, parse_mode='HTML')
                return
            price = product.find('div', {'class': 'card-price'}).text.replace('\n', '').strip()
            text += f'💵Цена: {price}\n'
            text += f'✅{exist}\n'
            text += f'{product_name}\n\n'
    if counter == 0:
        text += f'<b>part33.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    final = f'<b>part33.ru</b>\n\n'
    final += text
    await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')


async def arlos(art, tel_id):
    print('ARLOS start', datetime.datetime.now())
    main_url = 'https://arlos.ru/'
    html = await get_html(f'https://arlos.ru/search/?q={art}&s=')
    bs = BeautifulSoup(html, 'lxml')
    products = bs.find_all('div', {'class': 'search-item'})
    text = ""
    final = ""
    firstly = True
    divided = False
    date = None
    counter = len(products)
    alreadyPrinted = 0
    first_message = None
    first_message_text = ""
    if counter == 0:
        text += f'<b>arlos.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        print('ARLOS end', datetime.datetime.now())
        return
    for product in products:
        if alreadyPrinted == 8:
            divided = True
            if firstly:
                final = f'<b>arlos.ru</b>\n\n'
                final += f"Найдено результатов: {counter}\n\n"
                firstly = False
            final += text
            alreadyPrinted = 0
            first_message_text = text
            text = ""
            first_message = await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')
            final = ""
        alreadyPrinted+=1
        link = f"{main_url}{product.find('a').get('href')}"
        name = product.find('a').text
        product_name = f'<a href="{link}">{name}</a>'
        newHtml = await get_html(link)
        innerBs = BeautifulSoup(newHtml, 'lxml')
        exist = innerBs.find('div', {'class': 'text_ef_bo status ef_color_status list-group-item-success'})
        delivery = innerBs.find('div', {'class': 'text_ef_bo list-group-success status2 ef_color'})
        if exist is not None:
            exist = "В наличии"
        elif delivery is not None:
            date = innerBs.find('span', {'class': 'arrival_date1 data_postavri_arlos text_ef_bo'})
            date = date.text
            exist = "Товар в пути"
        else:
            counter-=1
            if counter == 0:
                text += f'<b>arlos.ru</b>\n\n'
                text += "❌Товара не найдено❌"
                await bot.send_message(tel_id, text, parse_mode='HTML')
                print('ARLOS end', datetime.datetime.now())
                return
            continue
        price = innerBs.find('div', {'class': 'item_current_price normal-price'})
        price = price.text
        text += f'💰Цена: {price} ₽\n'
        if exist == "Товар в пути":
            text += f'🚚{exist}\n'
            text+= f'📅Дата поставки: {date}\n'
        else:
            text += f'✅{exist}\n'
        text += f'{product_name}\n\n'
    if divided is False:
        final = f'<b>arlos.ru</b>\n\n'
        final += f"Найдено результатов: {counter}\n\n"
    final += text
    await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')
    if divided:
        final = f'<b>arlos.ru</b>\n\n'
        final += f"Найдено результатов: {counter}\n\n"
        final += first_message_text
        try:
            await bot.edit_message_text(final, tel_id, first_message.message_id, parse_mode='HTML', disable_web_page_preview=True)
        except Exception:
            print('MessageNotModified')
    print('ARLOS end', datetime.datetime.now())


async def arlos_fully(art, tel_id):
    main_url = 'https://arlos.ru/'
    html = await get_html(f'https://arlos.ru/search/?q={art}&s=')
    bs = BeautifulSoup(html, 'lxml')
    products = bs.find_all('div', {'class': 'search-item'})
    text = ""
    date = None
    counter = 0
    if counter == len(products):
        text += f'<b>arlos.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    for product in products:
        name = product.find('a').text.split(' ')
        article = name[len(name)-1]
        print(art, article)
        if art == article:
            counter += 1
            link = f"{main_url}{product.find('a').get('href')}"
            name = product.find('a').text
            product_name = f'<a href="{link}">{name}</a>'
            newHtml = await get_html(link)
            innerBs = BeautifulSoup(newHtml, 'lxml')
            exist = innerBs.find('div', {'class': 'text_ef_bo status ef_color_status list-group-item-success'})
            delivery = innerBs.find('div', {'class': 'text_ef_bo list-group-success status2 ef_color'})
            if exist is not None:
                exist = "В наличии"
            elif delivery is not None:
                date = innerBs.find('span', {'class': 'arrival_date1 data_postavri_arlos text_ef_bo'})
                date = date.text
                exist = "Товар в пути"
            else:
                text += f'<b>arlos.ru</b>\n\n'
                text += "❌Товара не найдено❌"
                await bot.send_message(tel_id, text, parse_mode='HTML')
                return
            price = innerBs.find('div', {'class': 'item_current_price normal-price'})
            price = price.text
            text += f'💰Цена: {price} ₽\n'
            if exist == "Товар в пути":
                text += f'🚚{exist}\n'
                text += f'📅Дата поставки: {date}\n'
            else:
                text += f'✅{exist}\n'
            text += f'{product_name}\n\n'
    if counter == 0:
        text += f'<b>arlos.ru</b>\n\n'
        text += "❌Товара не найдено❌"
        await bot.send_message(tel_id, text, parse_mode='HTML')
        return
    final = f'<b>arlos.ru</b>\n\n'
    final += text
    await bot.send_message(tel_id, final, disable_web_page_preview=True, parse_mode='HTML')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)