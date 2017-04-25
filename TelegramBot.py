#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# https://geekytheory.com/telegram-programando-un-bot-en-python/
# https://bitbucket.org/master_groosha/telegram-proxy-bot/src/07a6b57372603acae7bdb78f771be132d063b899/proxy_bot.py?at=master&fileviewer=file-view-default

# https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/types.py


import datetime

import telebot  # Importamos la librería
from telebot import types  # Y los tipos especiales de esta
from telebot import util

from connect_sqlite import conectionSQLite, ejecutaScriptSqlite

'''
def datosIniciales():
    with open(r'{}/id.conf'.format(directorio_local), 'r') as f:
        id_fich = f.readline().replace('/n', '')

    query = 'SELECT * FROM Configuraciones, Credenciales WHERE ID LIKE {} LIMIT 1'.format(id_fich)
    return conectionSQLite(ruta_db, query, True)[0]


credenciales = datosIniciales()'''
administrador = 33063767
usuariosPermitidos = [33063767, 40522670]
api_bot = "368596920:AAEkHLr8Anr4YaWW9JCMFuWTN9FlzBccjxs"
bot = telebot.TeleBot(api_bot)
db = "recordatorios.db"
# pass_transmission = credenciales['pass_transmission']
modo_debug = True
dicc_botones = {
    'mostrar_recordatorios': '/mostrar_recordatorios',
    'crear_recordatorio': '/crear_recordatorio',
    'borrar_recordatorio': '/borrar_recordatorio',
    'rar': '/descomprime',
    'sys': '/reboot_system',
    'ts': '/reboot_transmission',
    'exit': '/exit',
}

temporizador = {
    'fecha': str(),
    'hora': str(),
    'msg': str()
}


def getCodMsg():
    query = "SELECT CodMsg FROM Mensajes ORDER BY CodMsg DESC LIMIT 1"
    respuesta = conectionSQLite(db, query, True)
    print(respuesta)
    if len(respuesta) == 0:
        return 1
    return int(respuesta[0]["CodMsg"])


def getCodTemp():
    query = "SELECT CodTemp FROM Temporizador ORDER BY CodTemp DESC LIMIT 1"
    respuesta = conectionSQLite(db, query, True)
    if modo_debug:
        print(respuesta)
    if len(respuesta) == 0:
        return 1
    return int(respuesta[0]["CodTemp"])


def getMsg(codUser):
    query = "SELECT Mensajes.Mensaje, Mensajes.Adjunto, Temporizador.fecha, Temporizador.hora FROM Mensajes \
            INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
            INNER JOIN Temporizador ON Mensajes.CodTemp = Temporizador.CodTemp \
            WHERE Usuarios.Id LIKE '{}'".format(codUser)

    respuesta = conectionSQLite(db, query, True)
    print(respuesta)
    return respuesta


def checkUsers(usuario, alias):
    query = "SELECT * FROM Usuarios WHERE Id LIKE '{}'".format(usuario)
    respuesta = conectionSQLite(db, query, True)
    if modo_debug:
        print(respuesta)
        print(len(respuesta))
    if len(respuesta) == 0:
        query = "INSERT INTO Usuarios (Id, Name) VALUES ('{}', '{}')".format(usuario, alias)
        if modo_debug:
            print(query)
        conectionSQLite(db, query)
        return checkUsers(usuario, alias)

    return respuesta[0]["CodUser"]


@bot.message_handler(commands=["start"])
def command_start(message):
    bot.send_message(message.chat.id, "Bienvenido al bot\nTu id es: {}".format(message.chat.id))


@bot.message_handler(commands=["help"])
def command_help(message):
    bot.send_message(message.chat.id, "Aqui pondre todas las opciones")
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Github', url="https://github.com/procamora/Gestor-Series")
    itembtnv = types.InlineKeyboardButton('Documentacion',
                                          url="https://github.com/procamora/Gestor-Series/blob/master/README.md")
    markup.row(itembtna, itembtnv)
    bot.send_message(message.chat.id, "Aqui pondre todas las opciones", reply_markup=markup)


@bot.message_handler(func=lambda message: message.chat.id == administrador, commands=['mostrar_recordatorios'])
def mostrar_recordatorios(message):
    # Split the text each 3000 characters.
    # split_string returns a list with the splitted text.
    mensaje = str()
    for i in getMsg(message.chat.id):
        mensaje += "{}\n".format(i)

    splitted_text = util.split_string(mensaje, 3000)
    for text in splitted_text:
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['crear_recordatorio'])
def crear_recordatorio_fecha(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row((datetime.date.today() + datetime.timedelta(days=0)).strftime("%d-%m-%y"))
    markup.row((datetime.date.today() + datetime.timedelta(days=1)).strftime("%d-%m-%y"))
    markup.row((datetime.date.today() + datetime.timedelta(days=2)).strftime("%d-%m-%y"))
    markup.row((datetime.date.today() + datetime.timedelta(days=3)).strftime("%d-%m-%y"))
    bot.send_message(message.chat.id, "Introduce la fecha del recordatorio ", reply_markup=markup)

    bot.register_next_step_handler(message, crear_recordatorio_hora)


def crear_recordatorio_hora(message):
    temporizador['fecha'] = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row("09:00", "11:00")
    markup.row("13:00", "15:00", "18:00")
    markup.row("20:00", "22:00")
    bot.send_message(message.chat.id, "Introduce la hora del recordatorio ", reply_markup=markup)

    bot.register_next_step_handler(message, crear_recordatorio_texto)


def crear_recordatorio_texto(message):
    temporizador['hora'] = message.text
    bot.send_message(message.chat.id,
                     "El la fecha a guardar es: {} - {}".format(temporizador['fecha'], temporizador['hora']))

    bot.send_message(message.chat.id, "Introduce el mensaje a guardar")
    bot.register_next_step_handler(message, ejecutar_recordatorio_texto)


def ejecutar_recordatorio_texto(message):
    userID = checkUsers(message.chat.id, message.chat.username)
    print(userID)

    nextCodTemp = getCodTemp() + 1
    nextCodMsg = getCodMsg() + 1

    if userID is not None:
        query = "INSERT INTO Temporizador (CodTemp, fecha, hora) VALUES ({}, '{}', '{}');\n \
                ".format(nextCodTemp, temporizador['fecha'], temporizador['hora'])
        # adjuntos de momento no lo uso
        query += "INSERT INTO Mensajes (CodMsg, CodUser, CodTemp, Mensaje) VALUES ({}, {}, {}, '{}') \
                 ".format(nextCodMsg, userID, nextCodTemp, message.text)
        if modo_debug:
            print(query)
            ejecutaScriptSqlite(db, query)


# Con esto, le decimos al bot que siga funcionando incluso si encuentra
# algun fallo.
bot.polling(none_stop=True)
