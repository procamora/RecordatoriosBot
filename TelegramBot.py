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
import urllib
import logging
import re

import telebot  # Importamos la librería
from telebot import types  # Y los tipos especiales de esta
from telebot import util

from connect_sqlite import conectionSQLite, ejecutaScriptSqlite

config = configparser.ConfigParser()
config.sections()
config.read('/home/pi/RecordatoriosBot/recordatorios.conf')

db = config['PI']['db']
admin = config['PI']['administrador']

bot = telebot.TeleBot(config['PI']['bot_token'])
#bot.send_message(admin ,"Inicio servidor")

CANCELAR = "exit"

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

mensajeHelp = "Si vas a crear una crear un recordatorio con una fecha u hora que no aparezca en \
los botones sigue esta estructura:\nfecha: dd-mm-yyyy Ejemplo: 09-12-2017\n hora: hh:mm \
Ejemplo: 16:00.\nEl bot esta en desarrollo por lo que puede tener fallos, no me hago responsable si \
falla a la hora de recordate algo."



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
    query = "SELECT Usuarios.Name, Usuarios.Id ,Mensajes.Mensaje, Mensajes.Adjunto, \
            Mensajes.Activo, Temporizador.fecha, Temporizador.hora, Mensajes.CodMsg FROM Mensajes \
            INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
            INNER JOIN Temporizador ON Mensajes.CodTemp = Temporizador.CodTemp \
            WHERE Usuarios.Id LIKE '{}' AND Mensajes.Activo LIKE 1".format(codUser)

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

def cancela(message):
    bot.reply_to(message, "Accion cancelada", reply_markup=markupInicio)



@bot.message_handler(commands=["start"])
def command_start(message):
    bot.send_message(message.chat.id, "Bienvenido al bot\nTu id es: {}".format(message.chat.id))

    bot.reply_to(message, mensajeHelp)
    bot.reply_to(message, "Esta es la lista de comandos disponibles", reply_markup=markupInicio)


@bot.message_handler(commands=["help"])
def command_help(message):
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Github', url="https://github.com/procamora/GRecordatoriosBot")
    itembtnv = types.InlineKeyboardButton('README',
                                          url="https://github.com/procamora/RecordatoriosBot/blob/master/README.md")
    markup.row(itembtna, itembtnv)
    #bot.reply_to(message, "La lista de comandos disponibles es:\n/mostrar_recordatorios\n/crear_recordatorio", reply_markup=markup)
    bot.reply_to(message, "He sido creado por @procamora\n{}".format(mensajeHelp))
    bot.reply_to(message, "Esta es la lista de comandos disponibles", reply_markup=markupInicio)


@bot.message_handler(commands=['mostrar_recordatorios'])
def mostrar_recordatorios(message):
    # Split the text each 3000 characters.
    # split_string returns a list with the splitted text.
    mensaje = str()
    consultaSql =  getMsg(message.chat.id)
    if consultaSql is None:
        bot.reply_to(message, "No tienes recordatorios pendientes")
        return
    
    # si hay mensajes
    for i in consultaSql:
        mensaje += "Mensaje: {}, Fecha: {} {}\n".format(i["Mensaje"], i["fecha"], i["hora"])

    splitted_text = util.split_string(mensaje, 3000)
    if len(splitted_text) == 0:
        bot.reply_to(message, "No tienes recordatorios pendientes", reply_markup=markupInicio)
    else:
        for text in splitted_text:
            bot.reply_to(message, text)
    
    print(int(message.chat.id) == int(admin))
    print(message.chat.id)
    print(admin)
    if int(message.chat.id) == int(admin):
        mostrar_recordatorios_admin(message)


def mostrar_recordatorios_admin(message):
    # Split the text each 3000 characters.
    # split_string returns a list with the splitted text.
    print("admin")
    mensaje = str()
    mensaje += "Mensajes de todos:\n"
    consultaSql =  getMsg("%") # todos los mensajes
    if consultaSql is None:
        bot.reply_to(message, "Nadie tiene recordatorios pendientes")
        return
    
    # si hay mensajes
    for i in consultaSql:
        mensaje += "User: {}, ID: {}, Mensaje: {}, Fecha: {} {}\n\n".format(i["Name"], i["Id"], i["Mensaje"], i["fecha"], i["hora"])

    splitted_text = util.split_string(mensaje, 3000)
    if len(splitted_text) == 0:
        bot.reply_to(message, "Nadie tiene recordatorios pendientes", reply_markup=markupInicio)
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
    markup.row(CANCELAR)
    msg = bot.reply_to(message, "Introduce la fecha del recordatorio ", reply_markup=markup)

    bot.register_next_step_handler(msg, crear_recordatorio_hora, True)


def crear_recordatorio_hora(message, isRecordatorioFecha):
    """
    Metodo que parsea la hora del recordatorio, esta funcion es llamada desde crear_recordatorio_fecha donde tiene que 
    ejecutarse con normalidad preguntando por la hora o desde crear_recordatorio_texto que su unica funcion es 
    volver a llamar a crear_recordatorio_texto para que vuelva a introducir la hora correctamente
    
    :isRecordatorioFecha: Variable booleanda que indica si la funcion es llamada desde crear_recordatorio_fecha
    :return:
    """

    if message.text == CANCELAR: # si exit paramos
        cancela(message)
        return

    elif not isRecordatorioFecha:
        bot.register_next_step_handler(message, crear_recordatorio_texto)
        return

    elif not re.match(r"^\d+\-\d+\-\d+$", message.text):
        bot.reply_to(message, "Introduce una fecha CORRECTA :(")
        crear_recordatorio_fecha(message)

    else:
        temporizador['fecha'] = message.text.replace("/", "-")
        markup = types.ReplyKeyboardMarkup()
        markup.row("09:00", "11:00")
        markup.row("13:00", "15:00", "18:00")
        markup.row("20:00", "22:00")
        
        msg = bot.reply_to(message, "Introduce la hora del recordatorio ", reply_markup=markup)

        bot.register_next_step_handler(msg, crear_recordatorio_texto)


def crear_recordatorio_texto(message):
    if message.text == CANCELAR: # si exit paramos
        cancela(message)
        return

    elif not re.search(r"^\d+\:\d+$", message.text):
        bot.reply_to(message, "Introduce una hora CORRECTA :(")
        crear_recordatorio_hora(message, False)

    else:
        temporizador['hora'] = message.text
        bot.send_message(message.chat.id,
                         "El la fecha a guardar es: {} - {}".format(temporizador['fecha'], temporizador['hora']))

        markup = types.ReplyKeyboardMarkup()
        markup.row("Ir a comprar", "Tirar la basura")
        markup.row("Clase", "Tarea", "Estudiar")
        bot.reply_to(message, "Introduce el mensaje a guardar", reply_markup=markup)
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
        # FIXME adjuntos de momento no lo uso
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
    
    if recordatorio is None:
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
        markup.row(CANCELAR)

        bot.reply_to(message, "Diccionario de IDs", reply_markup=markup)

        bot.register_next_step_handler(msg, borrar_recordatorios_step2)


def borrar_recordatorios_step2(message):
    if message.text == CANCELAR: # si exit paramos
        cancela(message)
        return

    bot.reply_to(message, "En proceso de implementacion")

    #if len(message.text) == 0: da fallo
    #    return

    query = "DELETE FROM Mensajes \
            WHERE Mensaje IN ( \
                SELECT Mensaje FROM Mensajes \
                INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
                WHERE Usuarios.Id LIKE '{}' AND Mensajes.CodMsg LIKE '{}' )".format(message.chat.id, message.text)

    #bot.reply_to(message, query)
    respuesta = conectionSQLite(db, query, True)
    bot.reply_to(message, "Mensaje borrado", reply_markup=markupInicio)
    
    #if len(respuesta) != 0:
    #    bot.reply_to(message, "Este es el mensaje que se ha borrado: \n{}".format(respuesta[0]["Mensaje"]))


@bot.message_handler(commands=['error'])
def send_welcome(message):
    bot.reply_to(message, "Genero una excepcion, sino llega un segundo mensaje es que ha petado :(")
    raise ValueError('A very specific bad thing happened')
    bot.reply_to(message, "segundo mensaje :) BIEN!!")

"""
@bot.message_handler(func=lambda message: True)
def comando_desconocido(message):
    bot.reply_to(message, "Comando desconocido, comandos disponibles: ")
    command_help(message)
"""

def sacaDatos():
    query = """SELECT Usuarios.Id, Mensajes.Mensaje, Mensajes.Adjunto, Mensajes.Activo, Temporizador.fecha, \
    Temporizador.hora, Mensajes.CodMsg FROM Mensajes \
    INNER JOIN Usuarios ON Mensajes.CodUser = Usuarios.CodUser \
    INNER JOIN Temporizador ON Mensajes.CodTemp = Temporizador.CodTemp \
    WHERE Mensajes.Activo LIKE 1
    """
    return conectionSQLite(db, query, True)


def checkFechaHora(fecha, hora):
    """
    Metodo al que le pasamos una fecha/hora para que compruebe si es correcta
    :return boolean: indicando si la fecha/hora es correcta
    """

    if fecha != datetime.datetime.now().date().strftime("%d-%m-%Y"):
        return False

    if hora != datetime.datetime.now().strftime("%H:%M"):
        return False

    return True


def compruebaRecordatoriosAntiguos(fecha, hora, codMsg, datos):
    """
    Desabilita todos los recordarorios cuya fecha haya pasado
    """

    try:
        actual = datetime.datetime.now().date()
        fecha_actual = datetime.datetime(actual.year, actual.month, actual.day)
        fecha_final = datetime.datetime.strptime(fecha, "%d-%m-%Y")

        if modo_debug:
            print("compruebaRecordatoriosAntiguos")
            print(fecha_actual)
            print(fecha_final)
            print(fecha_final < fecha_actual)

        activo = True
        if fecha_final < fecha_actual:
            activo = False
        elif  fecha_final == fecha_actual and hora < datetime.datetime.now().strftime("%H:%M"):
            activo = False

        if not activo:
            query = "UPDATE Mensajes SET Activo=0 WHERE CodMsg LIKE {}".format(codMsg)
            conectionSQLite(db, query)
            if modo_debug:
                print(query)

            bot.send_message(datos["Id"], "He fallado en mi unica labor, no he podido entregarte este mensaje a tiempo :'(")
            bot.send_message(datos["Id"], datos["Mensaje"])
            bot.send_message(admin ,"Mensaje: {} desactualizado".format(codMsg))

    except: # sino conseguimos parsear el mensaje lo desactivamos
        query = "UPDATE Mensajes SET Activo=0 WHERE CodMsg LIKE {}".format(codMsg)
        conectionSQLite(db, query)

        if modo_debug:
            print(query)

        bot.send_message(datos["Id"], "He fallado en mi unica labor, no he podido entregarte este mensaje a tiempo :'(")
        bot.send_message(datos["Id"], datos["Mensaje"])
        bot.send_message(admin ,"Mensaje: {} desactualizado".format(codMsg))


def ejecutaRecordatorio(datos):
    """Envia el mensaje con el recordatorio y desabilita el recordatorio
    
    [description]
    
    Arguments:
        datos {[type]} -- [description]
    """

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
            try:
                compruebaRecordatoriosAntiguos(i["fecha"], i["hora"], i["CodMsg"], i)
                if checkFechaHora(i["fecha"], i["hora"]):
                    ejecutaRecordatorio(i)
            except:
                pass
        time.sleep(20)


d = threading.Thread(target=daemon, name='Daemon')
d.setDaemon(True)
d.start()

logger = telebot.logger
telebot.logger.setLevel(logging.INFO) # Outputs debug messages to console.

# Con esto, le decimos al bot que siga funcionando incluso si encuentra
# algun fallo.
try:
    bot.polling(none_stop=True, interval=0, timeout=3)
except urllib.error.HTTPError:
    time.sleep(10)

while True:
    time.sleep(20)
