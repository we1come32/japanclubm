from datetime import timedelta
from loguru import logger
from tortoise import Tortoise, fields, models
import tortoise
import settings


class User(models.Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    articles = fields.BooleanField(default=False)
    news = fields.BooleanField(default=False)
    stream = fields.BooleanField(default=False)
    manga = fields.BooleanField(default=False)
    animation = fields.BooleanField(default=False)
    history = fields.BooleanField(default=False)
    last_message = fields.DatetimeField(default=lambda: (tortoise.timezone.now() - timedelta(days=1, minutes=5)))
    admin = fields.BooleanField(default=False)

    def __str__(self):
        return f'User {self.user_id}'


async def on_startup():
    logger.debug('Устанавливаем соединение с базой данных...')
    await Tortoise.init(
        db_url=f'sqlite://{settings.BASE_DIR}/db.sqlite3',
        modules={'models': ['bot']}
    )
    await Tortoise.generate_schemas()
    logger.debug('Соединение с базой данных установлено')


async def on_shutdown():
    logger.debug('Закрываем соединение с базой данных...')
    await Tortoise.close_connections()
    logger.debug('Соединение с базой данных закрыто')
