import config
import telebot as tb
import re
import psycopg2 as psc


def exec_query(query: str) -> "list[tuple[str]]":
    with psc.connect(dbname=config.dbname, user=config.dbuser) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query);
            connection.commit()
            res = cursor.fetchall()
    return res

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

    info = list(map(lambda x: x.strip(), message.text.split("\n")))
        
    if len(info) != 6:
        bot.send_message(message.chat.id, "Неправильный формат, нужно ровно 6 строк как в примере\nМожешь написать /help, чтобы увидеть пример")
        return
        
    if not re.fullmatch("(С )?\d\d(:|\.)\d\d( до \d\d(.|:)\d\d)?", info[0]):
        bot.send_message(message.chat.id, "Неправильный формат времени, надо вот так:\nC <начальное время> до <конечное время( необязательно )>\nМожешь написать /help, чтобы посмотреть пример")
        return
        
    if not re.fullmatch("\d\d? \w+ \d{4}", info[1]):
        bot.send_message(message.chat.id, "Неправильный формат даты, надо вот так:\n <число> <месяц> <год>\nМожешь написать /help, чтобы посмотреть пример")
        return

    if not (info[2] and info[3] and info[4]):
        bot.send_message(message.chat.id, "Надо написать название, описание и место, можешь посмотреть пример, написав /help")
        return

    if info[5].lower() not in ["музыка", "сходка", "иное"]:
        bot.send_message(message.chat.id, "Неправильная категория, можно только что-то из этого: музыка, сходка, иное\nМожешь написать /help, чтобы посмотреть пример")
        return
    
    try:
        exec_query(f"""insert into news (time, date, name, description, place, category) values ('{info[0]}', '{info[1]}', '{info[2]}', '{info[3]}', '{info[4]}', '{info[5]}')""")
    except psc.ProgrammingError:
        pass

    bot.send_message(message.chat.id, "Все хорошо, записал")
    bot.send_message(config.channel_id, f"""Название: "{info[2]}"
Описание: {info[3]}
Когда: {'В' if len(info[1]) == 5 else ''}{info[1]}
Где: {info[4]}
Категория: {info[5]}""")

bot.polling(non_stop=True)

