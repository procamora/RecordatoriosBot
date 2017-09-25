# RecordatoriosBot


* [ ] CAMBIAR -    if len(recordatorio) == 0  POR  if recordatorio is None:


cron para que se reinicie si tiene algun fallo

*/2 *   * * *   root    sudo systemctl -q is-active mio_bot_recordatorios.service && echo YES || sudo systemctl restart mio_bot_recordatorios.service
