from ..handlers import Post
from ..database import User


@Post(name='articles')
async def articles():
    return await User.filter(articles=True)


@Post(name='news')
async def news():
    return await User.filter(news=True)


@Post(name='stream')
async def stream():
    return await User.filter(stream=True)


@Post(name='manga')
async def manga():
    return await User.filter(manga=True)


@Post(name='animation')
async def animation():
    return await User.filter(animation=True)


@Post(name='history')
async def history():
    return await User.filter(history=True)


