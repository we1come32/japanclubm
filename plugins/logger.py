import sys
import loguru
from loguru import logger
from io import StringIO
import aiohttp
import vkbottle
from vkbottle import API

import settings


class LogFilter:
    """
    Фильтрация логов по уровню

    В примере ниже в файл file.log не попадут логи ниже уровня WARNING:
    loguru.logger.add(
        'file.log',
        filter=LogFilter(
            logger.level("WARNING").no
        )
    )
    """
    _min_level: int

    def __init__(self, min_level: int = 0):
        self._min_level = min_level

    def __call__(self, record: dict):
        return record["level"].no >= self._min_level


# Logging with message in VKontakte
async def log_handler(event: loguru._handler.Message):
    logFile = StringIO(event)
    logFile.name = 'file.log'
    api = API(token=settings.TOKEN)
    server_url = await api.docs.get_messages_upload_server(type='doc', peer_id=settings.DEV_USER_ID)
    async with aiohttp.ClientSession() as session:
        async with session.post(server_url.upload_url, data={'file': logFile}) as response:
            file = await response.json()
    doc_information = await api.docs.save(file['file'], title='File', tags='logs,логи,лог,log')
    message_id = await api.messages.send(
        message=f"Кожаный ублюдок, ты долбаеб\n\nЛоги прикладываю:",
        attachment=f"doc{doc_information.doc.owner_id}_{doc_information.doc.id}",
        random_id=0,
        peer_id=settings.DEV_USER_ID
    )
    try:
        await api.messages.delete(message_ids=[message_id])
    except vkbottle.VKAPIError:
        pass
    return True

logger.configure(
    handlers=[
        {"sink": 'logs/{time:YYYY-MM-DD}_INFO.log', "filter": LogFilter(logger.level("INFO").no)},
        {"sink": log_handler, "filter": LogFilter(logger.level("WARNING").no)},
    ]
)

if settings.DEBUG:
    logger.add(sys.stdout, level='DEBUG')
"""
logger.add('logs/{time:YYYY-MM-DD}_INFO.log', filter=LogFilter(logger.level("INFO").no))
logger.add(log_handler, filter=LogFilter(logger.level("WARNING").no))
"""
