import config
import telebot as tb
import re
import psycopg2 as psc


def check_data(message, info: list[str]) -> bool:
    if len(info) != 6:
        bot.send_message(message.chat.id, "Неправильный формат, нужно ровно 6 строк как в примере\nМожешь написать /help, чтобы увидеть пример")
        return False
        
    if not re.fullmatch("(С )?\d\d(:|\.)\d\d( до \d\d(.|:)\d\d)?", info[0]):
        bot.send_message(message.chat.id, "Неправильный формат времени, надо вот так:\nC <начальное время> до <конечное время( необязательно )>\nМожешь написать /help, чтобы посмотреть пример")
        return False
        
    if not re.fullmatch("\d\d? \w+ \d{4}", info[1]):
        bot.send_message(message.chat.id, "Неправильный формат даты, надо вот так:\n <число> <месяц> <год>\nМожешь написать /help, чтобы посмотреть пример")
        return False

    if not (info[2] and info[3] and info[4]):
        bot.send_message(message.chat.id, "Надо написать название, описание и место, можешь посмотреть пример, написав /help")
        return False

    if info[5].lower() not in ["музыка", "сходка", "иное"]:
        bot.send_message(message.chat.id, "Неправильная категория, можно только что-то из этого: музыка, сходка, иное\nМожешь написать /help, чтобы посмотреть пример")
        return False
    return True
    

def exec_query(query: str) -> "list[tuple[str]]":
    with psc.connect(dbname=config.dbname, user=config.dbuser) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query);
            connection.commit()
            res = cursor.fetchall()
    return res

def get_and_check_event_name(message) -> None:
    names = exec_query("select name from news")
    if (message.text.lower(), ) not in names:
        bot.send_message(message.chat.id, "Нет такого мероприятия")
        return
    
    bot.send_message(message.chat.id, "Введи исправленный вариант полностью. Введи /help, чтобы увидеть пример, если не помнишь точно формат записи")
    bot.register_next_step_handler(message, change_info_and_post)

def change_info_and_post(message) -> None:
    info = list(map(lambda x: x.strip(), message.text.split("\n")))
    
    if not check_data(message, info):
        return
    
    try: 
        exec_query(f"""update news set \"time\" = '{info[0]}',
                                         date = '{info[1]}',
                                         name = '{info[2]}',
                                         description = '{info[3]}',
                                         place = '{info[4]}',
                                         category = '{info[5]}'
                                         where name = '{message.text.lower()}'""")
    except psc.ProgrammingError:
        pass

    bot.send_message(message.chat.id, "Все хоpошо, записал")

    bot.send_message(config.channel_id, f"""ОБНОВЛЕНИЕ В МЕРОПЯТИИ: "{info[2]}"\n
Описание: {info[3]}\n
Когда: {'В' if len(info[1]) == 5 else ''}{info[1]}\n
Где: {info[4]}\n
Категория: {info[5]}""")

bot = tb.TeleBot(config.token)

@bot.message_handler(commands=["start", "help"])
def say_hi(message):
    bot.send_message(message.chat.id, "Привет\nФормат следующий:")
    bot.send_message(message.chat.id, "C <начальное время( обязательно )> до <конечное время( необязательно )>\n<число> <месяц( не цифрами )> <год>\nНазвание\nОписание\nМесто\nКатегория")
    bot.send_message(message.chat.id, "Название, описание и место писать без переносов строк\nКатегории только такие: музыка, сходки, иное")
    bot.send_message(message.chat.id, "Пример:")
    bot.send_message(message.chat.id, "С 12:00 до 18:00\n24 ноября 2024\nКрутое событие\nЭто событие будет во истину крутым, все приходите\nУлица Пушкина, 10\nМузыка")
    bot.send_message(message.chat.id, "Другой пример:")
    bot.send_message(message.chat.id, "12.00\n12 ноября 2024\nХорошее мероприятие\nРеально хорошее мероприятие\nТРЦ Солнышко\nИное")


@bot.message_handler(content_types=["text"])
def main(message):
    if message.from_user.username not in config.users:
        return
    
    if message.text.lower() == "изменить" and message.from_user.username in config.admins:
        bot.send_message(message.chat.id, "Напиши название мероприятия")
        bot.register_next_step_handler(message, get_and_check_event_name)
        return

    info = list(map(lambda x: x.strip(), message.text.split("\n")))

    if not check_data(message, info):
        return
    
    try:
        exec_query(f"""insert into news (time, date, name, description, place, category) 
                       values ('{info[0].lower()}', '{info[1].lower()}', '{info[2].lower()}', '{info[3].lower()}', '{info[4].lower()}', '{info[5].lower()}')""")
    except psc.ProgrammingError:
        pass

    bot.send_message(message.chat.id, "Все хорошо, записал")
    bot.send_message(config.channel_id, f"""Название: "{info[2]}"\n
Описание: {info[3]}\n
Когда: {'В' if len(info[1]) == 5 else ''}{info[1]}\n
Где: {info[4]}\n
Категория: {info[5]}""")

bot.polling(non_stop=True)

