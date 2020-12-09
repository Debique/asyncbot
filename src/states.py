from aiogram.dispatcher.filters.state import State, StatesGroup

class ArticleFinder(StatesGroup):
    waiting_full_search = State()
    waiting_partly_search = State()
    main_menu = State()
