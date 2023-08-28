# OOO QUIZ LTD 

Бот для квизов. Демо-боты: [telegram](http://t.me/ooo_quiz_ltd_bot), [vk](https://vk.com/im?sel=-219035967).

## Установка и настройка

### Установка зависимостей
1. Создайте виртуальное окружение и установите в него необходимые библиотеки:
   ```commandline
   python3 -m venv venv
   venv/bin/pip install -U -r requirements.txt 
   ```
1. Создайте файл `.env` в корневой директории проекта по образцу `.env.sample`. 

### База данных Redis Cloud
1. Создайте базу данных на Redis Cloud ([инструкция](https://developer.redis.com/create/rediscloud/)).
2. Получите ключи доступа к ней и заполните соответствующие переменные в `.env`.

### Бот для Телеграма
1. Создайте бота через BotFather.
2. Добавьте его токен в переменную TG_TOKEN в файле `.env`

### Бот для ВК
1. Создайте сообщество
2. В настройках сообщества разрешите боту отправку сообщений
3. Добавьте токен бота в переменную VK_TOKEN в файле `.env`

### Вопросы для квиза
1. Получите архив с вопросами, распакуйте их и укажите полный путь 
к директории с файлами вопросов в переменной `QUESTION_DIR` в файле `.env` 
(по умолчанию это `data/quiz-questions/`).
2. Запустите скрипт `load_quiz_items.py`, чтобы загрузить вопросы в Redis. 
Количество вопросов определяется переменной окружения `QUESTION_LIMIT`.

## Использование
ВК-бот и телеграм-бот работают из файлов `vk_bot.py` и `tg_bot.py`.
Для параллельного запуска на сервере вам поможет утилита 
[screens](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Hosting-your-bot#start-your-bot) 
или [systemd](https://dvmn.org/encyclopedia/deploy/systemd-tutorial/).
