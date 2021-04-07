import json
import re
import plugins

from vkbottle import (GroupEventType, GroupTypes, Keyboard,
                      KeyboardButtonColor, LoopWrapper, Text, Callback)
from vkbottle.bot import Bot, Message
from vkbottle import VKAPIError
from tortoise import timezone
from datetime import timedelta

import settings

from plugins.database import User, on_shutdown, on_startup

from plugins.actions import *
from plugins.handlers import Category
from plugins.logger import logger


loop_wrapper = LoopWrapper()
loop_wrapper.on_startup.append(on_startup())
loop_wrapper.on_shutdown.append(on_shutdown())
bot = Bot(settings.TOKEN, loop_wrapper=loop_wrapper)

# Отключение привязки к
bot.labeler.vbml_ignore_case = True


menu_message = 'Выберите пункт меню:'


# Создали меню
menu = Category(name="menu", name_ru="Меню", color=KeyboardButtonColor.PRIMARY)

# Создали первую категорию меню - Рассылка
newsletter = Category(name="newsletter", name_ru="Управление рассылкой", color=KeyboardButtonColor.SECONDARY)
# оздали вторую категорию меню - Статистика
statistics = Category(name='statistic', name_ru="Статистика подписок", color=KeyboardButtonColor.SECONDARY,
                      allow=(lambda user: user.admin), action=StatisticAction)
menu.add(newsletter)
menu.add(statistics)

# Создаем рассылки
newsletter.add(Category(name='articles', name_ru='Статьи', action=ArticlesAction))
newsletter.add(Category(name='news', name_ru='Новости', action=NewsAction))
newsletter.add(Category(name='streams', name_ru='Стримы', action=StreamsAction))
newsletter.add(Category(name='manga', name_ru='Манга', action=MangaAction))
newsletter.add(Category(name='animation', name_ru='Анимации', action=AnimationAction))
newsletter.add(Category(name='history', name_ru='Истории', action=HistoryAction))


@bot.on.raw_event(GroupEventType.WALL_POST_NEW, dataclass=GroupTypes.WallPostNew)
@logger.catch
async def wall_post_new_handler(event: GroupTypes.WallPostNew):
    """
    Обработчик новых новостей
    :param event: Ивент отправленного поста на стенку
    :return: None
    """

    # Поиск категории отправленного поста
    post_filter = ''.join(
        f"{_['name']}|"
        for _ in plugins.handlers.Post.registered
    )[:-1]
    result = re.search(post_filter, event.object.text)

    logger.debug("Filter:" + post_filter)
    logger.debug("Post text:" + event.object.text)
    logger.debug(f"Result: {result}")
    # Если категория найдена
    if result is not None:
        post_type = result.group(0)
        # Идет поиск чувачков, которые подписаны на нужную категорию
        users = []
        short_name = ''
        for post_handler in plugins.handlers.Post.registered:
            if post_type == post_handler['name']:
                users += await post_handler['action']()
                short_name = post_handler['short_name']

        # Подготовка к рассылке
        # - Создание клавиатуры для отписки
        keyboard = Keyboard(inline=True)
        keyboard.add(Callback("Отписаться", payload={'cmd': f"actions.{short_name}"}), color=KeyboardButtonColor.NEGATIVE)
        # - Создание вложения
        attachment = f"wall{event.object.owner_id}_{event.object.id}"

        # Старт рассылки
        for user in users:
            try:
                await bot.api.messages.send(
                    user.user_id, attachment=attachment,
                    random_id=0,
                    keyboard=keyboard.get_json()
                )
            except BaseException as e:
                pass


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=GroupTypes.MessageEvent)
@logger.catch
async def handle_message_event(event: GroupTypes.MessageEvent):
    """
     Логика по обработке нажатий на кнопки (не рекомендую туда лазить, чинить трудно т.к. любое изменение
    может сломать программу)
    :param event: Ивент нажатия на кнопку
    :return: Всегда возвращает None
    """
    user_id = event.object.user_id
    user = await User.filter(user_id=user_id).first()
    payload = event.object.payload['cmd']
    local_logger = logger.bind(user_id=user_id)
    local_logger.debug(f'Получен payload={payload}')
    if payload == 'none':
        message = "Эта кнопка ничего не делает"
    elif payload.startswith('menu'):
        payload = payload.split('.')
        actions = await menu(user, 'menu', payload[1:] + [''])
        message = 'Меню обновлено'
        for action in actions:
            if action['action'] == 'edit':
                try:
                    messages = await bot.api.messages.get_by_conversation_message_id(
                        peer_id=event.object.peer_id,
                        conversation_message_ids=[event.object.conversation_message_id]
                    )
                    await bot.api.messages.delete(
                        message_ids=messages.items[0].id,
                        delete_for_all=True
                    )
                except VKAPIError:
                    logger.warning(f'Сообщение с conversation_message_id={event.object.conversation_message_id!r}, '
                                   f'peer_id={event.object.peer_id!r} не удалено. Возможно, оно уже было удалено ранее')
                await bot.api.messages.send(
                    peer_id=event.object.peer_id,
                    message=menu_message if action['text'] is None else action['text'],
                    # conversation_message_id=event.object.conversation_message_id,
                    random_id=0,
                    keyboard=action['keyboard'].get_json()
                )
            elif action['action'] == 'say':
                message = action['text']
    elif payload.startswith('actions'):
        payload = payload.split('.')[1:] + ['']
        try:
            function = newsletter.subcategories[payload[0]]
            if function.action is not None:
                color = await function.action.get_color(user)
            else:
                color = function.color
            if color == KeyboardButtonColor.POSITIVE:
                result = await function.action(user)
                message = result[1]
                await bot.api.messages.send(user_id=user.user_id, message=message, random_id=0)
            else:
                message = "Вы уже отписались от этой новостной рассылки"
        except KeyError as e:
            print(e)
            message = "Такой категории подписки не найдено"
    else:
        message = "Извините, произошла неизвестная ошибка"
        await bot.api.messages.send(user_id=settings.DEV_USER_ID, random_id=0,
                                    message=f"Неизвестная перегрузка {payload}")
    await bot.api.messages.send_message_event_answer(
        event_id=event.object.event_id,
        user_id=event.object.user_id,
        peer_id=event.object.peer_id,
        event_data=json.dumps({'type': 'show_snackbar', 'text': message}),
    )


def user_registered(function):
    """
    Декоратор для регистрации пользователя в базе данных и автоматической идентификации пользователя в системе
    :param function: Декорируемая функция
    :return: decorator - Декоратор переданной функции
    """
    async def decorator(message: Message, **kwargs):
        user_id = message.from_id
        user = await User.filter(user_id=user_id).first()
        if user is None:
            user = await User.create(user_id=user_id)
        await function(message=message, user=user, **kwargs)
    return decorator


@bot.on.private_message(text='начать')
@logger.catch
@user_registered
async def start_message(message: Message, user: User):
    """
    Стартовое сообщение
    :param message: Сообщение с текстом "Начать"
    :param user: Объект базы данных пользователя, отправившего это сообщение
    :return: None
    """
    keyboard = Keyboard(one_time=False)
    keyboard.add(Text(label='Меню', payload=''), color=KeyboardButtonColor.PRIMARY)
    msg = "Привет! Ты попал в группу Клуба японской культуры РТУ МИРЭА\n\n" \
          "Чтобы посмотреть меню, ты можешь в любое время написать мне \"Меню\", либо нажать на кнопку ниже"
    await message.answer(msg, keyboard=keyboard.get_json())


@bot.on.private_message(text=['меню', '/меню'])
@logger.catch
@user_registered
async def command_menu(message: Message, user: User):
    """
    Функция отправки сообщения с клавиатурой меню
    :param message: Сообщение в виде команды "Меню"
    :param user: Объект базы данных пользователя, отправившего это сообщение
    :return: None
    """
    actions = await menu(user, 'menu', [''])
    keyboard = actions[0]['keyboard'].get_json()
    await message.answer(menu_message, keyboard=keyboard)


@bot.on.private_message(text=['рассылка', '/рассылка'])
@logger.catch
@user_registered
async def newsletter_menu(message: Message, user: User):
    """
    Функция отправки сообщения с клавиатурой меню
    :param message: Сообщение в виде команды "Меню"
    :param user: Объект базы данных пользователя, отправившего это сообщение
    :return: None
    """
    actions = await newsletter(user, 'menu.newsletter', [''])
    keyboard = actions[0]['keyboard'].get_json()
    await message.answer(menu_message, keyboard=keyboard)


@bot.on.private_message()
@logger.catch
@user_registered
async def messages_handler(message: Message, user: User):
    """
    Функция отправки сообщения с клавиатурой меню
    :param message: Сообщение пользователя
    :param user: Объект базы данных пользователя, отправившего это сообщение
    :return: None
    """
    if message.text.lower() in ['меню', '/меню']:
        await command_menu(message)
    elif timezone.now() - user.last_message > timedelta(days=1):
        keyboard = Keyboard(one_time=False)
        keyboard.add(Text(label='Меню', payload=''), color=KeyboardButtonColor.PRIMARY)
        msg = "Привет.\nЕсли тебе нужно меню группы, нажми на соответствующую кнопку или напиши \"Меню\", " \
              "иначе просто продублируй вопрос чтобы модераторы могли на него ответить"
        user.last_message = timezone.now()
        await user.save()
        await message.answer(msg, keyboard=keyboard.get_json())


if __name__ == '__main__':
    bot.run_forever()
