# RecordatoriosBot


* [ ] CAMBIAR -    if len(recordatorio) == 0  POR  if recordatorio is None:


cron para que se reinicie si tiene algun fallo

- */2 *   * * *   root    sudo systemctl -q is-active mio_bot_recordatorios.service && echo YES || sudo systemctl restart mio_bot_recordatorios.service




```sql
BEGIN TRANSACTION;
CREATE TABLE "Usuarios" (
    `CodUser`   INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    `Id`    TEXT UNIQUE,
    `Name`  TEXT
);

CREATE TABLE "Temporizador" (
    `CodTemp`   INTEGER NOT NULL,
    `fecha` TEXT NOT NULL,
    `hora`  TEXT NOT NULL
);

CREATE TABLE "Mensajes" (
    `CodMsg`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    `CodUser`   INTEGER NOT NULL,
    `CodTemp`   INTEGER,
    `Mensaje`   NUMERIC NOT NULL,
    `Adjunto`   TEXT,
    `Activo`    TEXT NOT NULL DEFAULT 1
);

COMMIT;
```
