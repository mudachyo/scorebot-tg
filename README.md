> [!IMPORTANT]
> **Python Version 3.11.8**

# Запуск бота
## Установка Python:
1. Скачайте и установите последнюю версию Python 3.11.8 с официального сайта: https://www.python.org/downloads/release/python-3118/
2. Убедитесь, что при установке выбрана опция "Add Python to PATH".
## Установка зависимостей:
1. Откройте командную строку (`cmd.exe`).
2. Установите необходимые библиотеки с помощью `pip`:
3.  ``` pip install -r requirements.txt ```
## Настройка бота:
1. Откройте файл `bot.py` в текстовом редакторе.
2. Вставьте свой токен бота в переменную `API_TOKEN`.
3. Добавьте `ID` пользователей, которые будут иметь права администратора, в список `AUTHORIZED_USERS`.
## Запуск бота:
1. В командной строке выполните команду:  ```python main.py```

### Список команд
* `/start` - Запуск бота и вывод приветственного сообщения.
* `/totals` - Просмотр списка пользователей и их баллов, отсортированных по убыванию.
* `/top10` - Просмотр топ-10 пользователей с наибольшим количеством баллов.
* `/points` или `/score` - Просмотр текущего количества баллов пользователя, который отправил команду.
* `@username +10 Причина` - Добавление 10 баллов пользователю @username с указанием причины.
* `@username -10 Причина` - Вычитание 10 баллов у пользователя @username с указанием причины.
* `/history @username` - Просмотр истории изменений баллов для пользователя @username.

Административные команды (доступны только авторизованным пользователям):
* `/delete @username` - Удаление пользователя @username из базы данных.
* `/delete` - Вывод списка пользователей с кнопками для удаления.
* `/clear_all` - Очистка всего списка пользователей (требуется подтверждение).
* `/log` - Просмотр лог-файла бота.
* `/log_size` - Проверка размера лог-файла.

## Примечания
- Для работы бота требуется база данных `user_scores.db`, которая будет создана автоматически при первом запуске.
- Лог-файл бота `bot.log` содержит информацию о действиях пользователей и изменениях баллов.
- Размер лог-файла ограничен `10 КБ`. При превышении этого размера файл будет очищен.
- Административные команды доступны только пользователям, чьи `ID` указаны в списке `AUTHORIZED_USERS`.