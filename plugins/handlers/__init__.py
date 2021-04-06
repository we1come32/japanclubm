from vkbottle import (Keyboard, KeyboardButtonColor, Callback)
from ..logger import logger
from ..database import User


class Category:
    name: str
    name_ru: str
    subcategories: dict
    subcategories_list: list
    action = None
    color = None
    allow = True

    def __init__(self, name: str, name_ru: str, action=None, color=None, allow=True):
        self.name = name
        self.name_ru = name_ru
        self.action = action
        self.color = color
        self.subcategories_list = []
        self.subcategories = {}
        self.allow = allow

    async def get_color(self, user: User):
        if self.action is not None:
            return await self.action.get_color(user)
        return self.color

    async def __call__(self, user: User, cmd: str, category_list: list, number: int = 0, last_object=None):
        category_name = category_list[0]

        # Откат назад
        if category_name == 'back':
            result = {'status': 'back', 'result': []}

        # Открытие меню
        elif category_name == '':
            result = None

            # Если есть действие, идет выполнение действия и идет возврат назад
            if not (self.action is None):
                flag, text = await self.action(user)
                result = {
                    'status': 'back',
                    'result': [
                        {
                            'action': 'say',
                            'text': text
                        }
                    ]
                }

            # Иначе идет открытие меню
            else:
                keyboard = Keyboard(inline=True)
                # keyboard.add(Callback(self.name_ru, {"cmd": "none"}), color=KeyboardButtonColor.PRIMARY)
                count = 0
                for tmp_category in self.subcategories_list:
                    allow = tmp_category.allow
                    if callable(tmp_category.allow):
                        allow = tmp_category.allow(user)
                    if allow:
                        if count % 2 == 0:
                            keyboard.row()
                        keyboard.add(
                            Callback(
                                tmp_category.name_ru,
                                {
                                    "cmd": f'{cmd}.{tmp_category.name}'
                                }
                            ),
                            color=await tmp_category.get_color(user)
                        )
                        count += 1
                if number > 0:
                    keyboard.row()
                    keyboard.add(Callback("Назад", {"cmd": f'{cmd}.back'}), color=KeyboardButtonColor.SECONDARY)
                tmp_result = {
                    'action': 'edit',
                    # 'text': None,
                    'text': self.name_ru,
                    'keyboard': keyboard
                }
                result = {
                    'status': 'ok',
                    'result': [tmp_result] if result is None else [tmp_result, result],
                }

        # Вызов следующего меню и обработка меню там
        else:
            category = self.subcategories.get(category_name, None)

            # Если подкатегории такой нет, выкидываешься ошибка
            if category is None:
                result = {'status': 'error', 'description': 'Категория не найдена'}

            # А если есть, вызывается следующая категория и сохраняется её результат как
            # результат выполнения этой функции
            else:
                result = {
                    'status': 'ok',
                    'result': await category(
                        user=user,
                        cmd=f"{cmd}.{category.name}",
                        category_list=category_list[1:],
                        number=number + 1,
                        last_object=self
                    )
                }

        # Обработка результата
        # Если все ок, возвращается результат запроса
        if result['status'] == 'ok':
            return result['result']

        # Если надо сделать шаг назад, вызывается шаг назад
        elif result['status'] == 'back':
            result = await last_object.__call__(
                user=user,
                cmd=cmd[:cmd.rfind('.')],
                category_list=[''],
                number=number-1,
                last_object=last_object
            ) + result['result']
            return result

        # Если ошибка, пишется в логи ошибку
        elif result['status'] == 'error':
            logger.debug(f'Получен статус DEBUG. При возврате получен результат {result}')
            return []

        # Если дошло до сюда, це пизда ебаная
        logger.warning('Я хуй его знает как оно до сюда дошло, но это бан')
        return [
            {
                'action': 'edit',
                'text': 'Хуйня ебаная, чекай логи уебок'
            }
        ]

    def add(self, value):
        self.subcategories_list.append(value)
        self.subcategories[value.name] = value


class Action:
    def __init__(self, function):
        self._function = function

    async def get_color(self, user):
        flag = (await self._function(user, change=False))[0]
        if flag:
            return KeyboardButtonColor.POSITIVE
        elif flag is None:
            return KeyboardButtonColor.SECONDARY
        return KeyboardButtonColor.NEGATIVE

    async def __call__(self, user):
        return await self._function(user, change=True)

    async def get_value(self, user):
        return await self._function(user, change=False)


class Post:

    registered = []
    _name: str

    def __init__(self, name: str):
        self._name = name

    def __call__(self, function):
        self.registered.append({'name': f"#{self._name}@japanclubm", 'action': function, 'short_name': self._name})
        return function

