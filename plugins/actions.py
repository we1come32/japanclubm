from .database import User
from .handlers import Action
import settings
from vkbottle import API

api = API(token=settings.TOKEN)


@Action
async def ArticlesAction(user: User, change: bool = True):
    msg = "Вы подписались на рыссылки новых статей"
    if user.articles:
        msg = "Вы отписались от рассылки новых статей"
    if change:
        # await api.messages.send(peer_id=user.user_id, message=msg, random_id=0)
        user.articles = not user.articles
        await user.save()
    return user.articles, msg


@Action
async def NewsAction(user: User, change: bool = True):
    msg = "Вы подписались на рассылку новостей"
    if user.news:
        msg = "Вы отписались от рассылки новостей"
    if change:
        # await api.messages.send(peer_id=user.user_id, message=msg, random_id=0)
        user.news = not user.news
        await user.save()
    return user.news, msg


@Action
async def StreamsAction(user: User, change: bool = True):
    msg = "Вы подписались на рассылку информации о стримах"
    if user.streams:
        msg = "Вы отписались от рассылки информации о стримах"
    if change:
        # await api.messages.send(peer_id=user.user_id, message=msg, random_id=0)
        user.streams = not user.streams
        await user.save()
    return user.streams, msg


@Action
async def MangaAction(user: User, change: bool = True):
    msg = "Вы подписались на рассылку манги"
    if user.manga:
        msg = "Вы отписались от рассылки магни"
    if change:
        # await api.messages.send(peer_id=user.user_id, message=msg, random_id=0)
        user.manga = not user.manga
        await user.save()
    return user.manga, msg


@Action
async def HistoryAction(user: User, change: bool = True):
    msg = "Вы подписались на рассылку историй"
    if user.history:
        msg = "Вы отписались от рассылки историй"
    if change:
        # await api.messages.send(peer_id=user.user_id, message=msg, random_id=0)
        user.history = not user.history
        await user.save()
    return user.history, msg


@Action
async def AnimationAction(user: User, change: bool = True):
    msg = "Вы подписались на рассылку анимаций"
    if user.animation:
        msg = "Вы отписались от рассылки анимаций"
    if change:
        # await api.messages.send(peer_id=user.user_id, message=msg, random_id=0)
        user.animation = not user.animation
        await user.save()
    return user.animation, msg


@Action
async def StatisticAction(user: User, change: bool = True):
    if change:
        message = "Статистика по подпискам:\n\n"
        message += f"- Статьи: {await user.filter(articles=True).count()}\n"
        message += f"- Новости: {await user.filter(news=True).count()}\n"
        message += f"- Стримы: {await user.filter(streams=True).count()}\n"
        message += f"- Манга: {await user.filter(manga=True).count()}\n"
        message += f"- Анимации: {await user.filter(animation=True).count()}\n"
        message += f"- История: {await user.filter(history=True).count()}\n"
        await api.messages.send(user_id=user.user_id, random_id=0,
                                message=message)
    return None, "Статистика отправлена"


__all__ = ['ArticlesAction', 'NewsAction', 'StreamsAction', 'MangaAction', 'HistoryAction', 'AnimationAction',
           'StatisticAction']
