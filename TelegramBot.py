#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# https://geekytheory.com/telegram-programando-un-bot-en-python/
# https://bitbucket.org/master_groosha/telegram-proxy-bot/src/07a6b57372603acae7bdb78f771be132d063b899/proxy_bot.py?at=master&fileviewer=file-view-default

# https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/types.py

"""
start - Inicia el bot
help - Muestra los comandos disponibles
crear_recordatorio - Crea un recordatorio
mostrar_recordatorios - Muestra todos los recordatorios del usuario
borrar_recordatorio - Borra un recordatorio
"""

import datetime
import time
import configparser
import threading

import telebot  # Importamos la librería
from telebot import types  # Y los tipos especiales de esta
from telebot import util

from connect_sqlite import conectionSQLite, ejecutaScriptSqlite

config = configparser.ConfigParser()
config.sections()
config.read('/home/pi/RecordatoriosBot/recordatorios.conf')

db = config['DEFAULTS']['db']
bot = telebot.TeleBot(config['DEFAULTS']['bot_token'])

modo_debug = True
dicc_botones = {
    'mostrar_recordatorios': '/mostrar_recordatorios',
    'crear_recordatorio': '/crear_recordatorio',
    'borrar_recordatorio': '/borrar_recordatorio',
    'help': '/help',
    'start': '/start',
}

temporizador = {
    'fecha': str(),
    'hora': str(),
    'msg': str()
}

markupInicio = types.ReplyKeyboardMarkup(one_time_keyboard=False)
markupInicio.row(dicc_botones["mostrar_recordatorios"], dicc_botones["borrar_recordatorio"])
markupInicio.row(dicc_botones["crear_recordatorio"])
markupInicio.row(dicc_botones["help"], dicc_botones["start"])


def getCodMsg():
    query = "SELECT CodMsg FROM Mensajes ORDER BY CodMsg DESC LIMIT 1"
    respuesta = conectionSQLite(db, query, True)
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
    query = "SELECT Mensajes.Mensaje, Mensajes.Adjunto, Mensajes.Activo, Temporizador.fecha, Temporizador.hora, \
            Mensajes.CodMsg FROM Mensajes \
            INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
            INNER JOIN Temporizador ON Mensajes.CodTemp = Temporizador.CodTemp \
            WHERE Usuarios.Id LIKE '{}' AND Mensajes.Activo LIKE 1".format(codUser)

    respuesta = conectionSQLite(db, query, True)
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

    bot.reply_to(message, "Introduce la hora del recordatorio ", reply_markup=markupInicio)


@bot.message_handler(commands=["help"])
def command_help(message):
    bot.send_message(message.chat.id, "Aqui pondre todas las opciones")
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Github', url="https://github.com/procamora/GRecordatoriosBot")
    itembtnv = types.InlineKeyboardButton('README',
                                          url="https://github.com/procamora/RecordatoriosBot/blob/master/README.md")
    markup.row(itembtna, itembtnv)
    bot.reply_to(message, "Aqui pondre todas las opciones", reply_markup=markup)


@bot.message_handler(commands=['mostrar_recordatorios'])
def mostrar_recordatorios(message):
    # Split the text each 3000 characters.
    # split_string returns a list with the splitted text.
    mensaje = str()
    for i in getMsg(message.chat.id):
        mensaje += "Mensaje: {}, Fecha: {} {}\n".format(i["Mensaje"], i["fecha"], i["hora"])

    splitted_text = util.split_string(mensaje, 3000)
    if len(splitted_text) == 0:
        bot.reply_to(message, "No tienes recordatorios pendientes")
    else:
        for text in splitted_text:
            bot.reply_to(message, text)


@bot.message_handler(commands=['crear_recordatorio'])
def crear_recordatorio_fecha(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row((datetime.date.today() + datetime.timedelta(days=0)).strftime("%d-%m-%Y"),
               (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d-%m-%Y"))
    markup.row((datetime.date.today() + datetime.timedelta(days=2)).strftime("%d-%m-%Y"),
               (datetime.date.today() + datetime.timedelta(days=3)).strftime("%d-%m-%Y"))
    markup.row((datetime.date.today() + datetime.timedelta(days=4)).strftime("%d-%m-%Y"),
               (datetime.date.today() + datetime.timedelta(days=5)).strftime("%d-%m-%Y"))
    markup.row((datetime.date.today() + datetime.timedelta(days=6)).strftime("%d-%m-%Y"),
               (datetime.date.today() + datetime.timedelta(days=7)).strftime("%d-%m-%Y"))
    msg = bot.reply_to(message, "Introduce la fecha del recordatorio ", reply_markup=markup)

    bot.register_next_step_handler(msg, crear_recordatorio_hora)


def crear_recordatorio_hora(message):
    temporizador['fecha'] = message.text
    markup = types.ReplyKeyboardMarkup()
    markup.row("09:00", "11:00")
    markup.row("13:00", "15:00", "18:00")
    markup.row("20:00", "22:00")
    msg = bot.reply_to(message, "Introduce la hora del recordatorio ", reply_markup=markup)

    bot.register_next_step_handler(msg, crear_recordatorio_texto)


def crear_recordatorio_texto(message):
    temporizador['hora'] = message.text
    bot.send_message(message.chat.id,
                     "El la fecha a guardar es: {} - {}".format(temporizador['fecha'], temporizador['hora']))

    bot.reply_to(message, "Introduce el mensaje a guardar")
    bot.register_next_step_handler(message, ejecutar_recordatorio_texto)


def ejecutar_recordatorio_texto(message):
    userID = checkUsers(message.chat.id, message.chat.username)
    if modo_debug:
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

        bot.reply_to(message, "Recordatorio guardado con exito", reply_markup=markupInicio)


@bot.message_handler(commands=['borrar_recordatorio'])
def borrar_recordatorios(message):
    mensaje = "Introduce el ID del mensaje a borrar, o los ID separados por coma\n"
    recordatorio = getMsg(message.chat.id)
    
    if len(recordatorio) == 0:
        bot.reply_to(message, "No tienes recordatorios disponibles")
        return
    else:
        for i in recordatorio:
            mensaje += "ID: {}, Mensaje: {}\n".format(i["CodMsg"], i["Mensaje"])

        splitted_text = util.split_string(mensaje, 3000)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)

        # imprimos los mensajes con sus ID
        for text in splitted_text:
            msg = bot.reply_to(message, text)

        # PONER DE FORMA DINAMICA
        if len(recordatorio) == 9:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
            markup.add(str(recordatorio[3]["CodMsg"]), str(recordatorio[4]["CodMsg"]), str(recordatorio[5]["CodMsg"]))
            markup.add(str(recordatorio[6]["CodMsg"]), str(recordatorio[7]["CodMsg"]), str(recordatorio[8]["CodMsg"]))
        elif len(recordatorio) == 8:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
            markup.add(str(recordatorio[3]["CodMsg"]), str(recordatorio[4]["CodMsg"]), str(recordatorio[5]["CodMsg"]))
            markup.add(str(recordatorio[6]["CodMsg"]), str(recordatorio[7]["CodMsg"]))
        elif len(recordatorio) == 7:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
            markup.add(str(recordatorio[3]["CodMsg"]), str(recordatorio[4]["CodMsg"]), str(recordatorio[5]["CodMsg"]))
            markup.add(str(recordatorio[6]["CodMsg"]))
        elif len(recordatorio) == 6:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
            markup.add(str(recordatorio[3]["CodMsg"]), str(recordatorio[4]["CodMsg"]), str(recordatorio[5]["CodMsg"]))
        elif len(recordatorio) == 5:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
            markup.add(str(recordatorio[3]["CodMsg"]), str(recordatorio[4]["CodMsg"]))
        elif len(recordatorio) == 4:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
            markup.add(str(recordatorio[3]["CodMsg"]))
        elif len(recordatorio) == 3:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]), str(recordatorio[2]["CodMsg"]))
        elif len(recordatorio) == 2:
            markup.add(str(recordatorio[0]["CodMsg"]), str(recordatorio[1]["CodMsg"]))
        elif len(recordatorio) == 1:
            markup.add(str(recordatorio[0]["CodMsg"]))
        else:
            return

        bot.reply_to(message, "Diccionario de IDs", reply_markup=markup)

        bot.register_next_step_handler(msg, borrar_recordatorios_step2)


def borrar_recordatorios_step2(message):
    bot.reply_to(message, "En proceso de implementacion")

    if len(message.text) == 0:
        return

    query = "SELECT Mensajes.Mensaje, Mensajes.Adjunto, Mensajes.Activo, Temporizador.fecha, Temporizador.hora, \
                Mensajes.CodMsg FROM Mensajes \
                INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
                INNER JOIN Temporizador ON Mensajes.CodTemp = Temporizador.CodTemp \
                WHERE Mensajes.CodMsg LIKE {}".format(message.text)

    print(query)
    respuesta = conectionSQLite(db, query, True)
    if len(respuesta) != 0:
        bot.reply_to(message, "Este es el mensaje que se borrara \n{}".format(respuesta[0]["Mensaje"]))


def sacaDatos():
    query = """SELECT Usuarios.Id, Mensajes.Mensaje, Mensajes.Adjunto, Mensajes.Activo, Temporizador.fecha, \
    Temporizador.hora, Mensajes.CodMsg FROM Mensajes \
    INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
    INNER JOIN Temporizador ON Mensajes.CodTemp = Temporizador.CodTemp \
    WHERE Mensajes.Activo LIKE 1
    """
    return conectionSQLite(db, query, True)


def checkFecha(fecha, hora):
    """
    Metodo al que le pasamos una fehca y hora y compruebe si es correcta
    :return: 
    """

    if fecha != datetime.datetime.now().date().strftime("%d-%m-%Y"):
        return False

    if hora != datetime.datetime.now().strftime("%H:%M"):
        return False

    return True


def compruebaRecordatoriosAntiguos(fecha, codMsg):
    """
    Desabilita todos los recordarorios cuya fecha haya pasado
    """

    activo = True
    if fecha < datetime.datetime.now().date().strftime("%d-%m-%Y"):
        activo = False

    if not activo:
        query = "UPDATE Mensajes SET Activo=0 WHERE CodMsg LIKE {}".format(codMsg)
        conectionSQLite(db, query)
        if modo_debug:
            print(query)


def ejecutaRecordatorio(datos):
    bot.send_message(datos["Id"], datos["Mensaje"])
    query = "UPDATE Mensajes SET Activo=0 WHERE CodMsg LIKE {}".format(datos["CodMsg"])
    conectionSQLite(db, query)
    if modo_debug:
        print(query)


def daemon():
    """
    Demonio que va comprobando si tiene que ejecutarse un recordatorio
    :return: 
    """
    while True:
        for i in sacaDatos():
            print(i)
            compruebaRecordatoriosAntiguos(i["fecha"], i["CodMsg"])
            if checkFecha(i["fecha"], i["hora"]):
                ejecutaRecordatorio(i)
        print()
        print()
        print()
        print()
        print()
        time.sleep(30)


d = threading.Thread(target=daemon, name='Daemon')
d.setDaemon(True)
d.start()

# Con esto, le decimos al bot que siga funcionando incluso si encuentra
# algun fallo.
bot.polling(none_stop=True, interval=0, timeout=3)
