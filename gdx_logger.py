#!/usr/bin/env python
import logging
logging.basicConfig(format="%(asctime)-15s  %(message)s")
log = logging.getLogger('GoDirectReader')
log.setLevel(logging.DEBUG)

from gdx import gdx
import time
import sqlite3
import configparser


config = configparser.ConfigParser()
config.read('settings.ini')
config = dict(config.items('default'))
COMMIT_EVERY = int(config['commit_every_n_records'])

DB = sqlite3.connect(config['database'])
with DB:
    DB.execute("CREATE TABLE IF NOT EXISTS respiration (tstamp INTEGER, force_N NUMBER, respiration_bpm NUMBER)")

gdx = gdx.gdx()


def open_device():
    log.info('attempting to connect over USB')
    try:
        gdx.open_usb()
    except OSError as _:
        gdx.devices = []
        pass
    if not gdx.devices:
        log.info('attempting to connect over BLE')
        try:
            gdx.open_ble(config['device_id'])
        except OSError as _:
            return False
    # select sensors for GDX-RB 0K1007T6 BLE -41
    # 1: Force (N)
    # 2: Respiration Rate (bpm)
    # 4: Steps (steps)
    # 5: Step Rate (spm)
    gdx.select_sensors([1,2])
    gdx.start(int(config['sampling_period_ms']))
    return True


RETRY_LIMIT = 5
for nth_try in range(1, RETRY_LIMIT+1):
    open_device()
    if gdx.devices:
        break
    log.info('attempting device connect {} / {}'.format(nth_try, RETRY_LIMIT))
    time.sleep(5)

NRECORDS = 0
try:
    while 1:
        try:
            RETRY_LIMIT = 5
            measurements = gdx.read()
            tstamp = int(time.time())

            if measurements == None:
                time.sleep(3)
                continue

            log.info('receive: {}'.format(measurements))
            DB.execute(
                    'INSERT INTO Respiration VALUES (?, ?, ?)',
                    (tstamp, measurements[0], measurements[1]))

            NRECORDS += 1
            if NRECORDS % COMMIT_EVERY == 0:
                DB.commit()
                log.info('commiting to db; now {} records captured'.format(NRECORDS))
        except OSError:
            for nth_try in range(1, RETRY_LIMIT):
                log.error('lost connection; retrying {} / {}'.format(nth_try, RETRY_LIMIT))
                if open_device():
                    break
                else:
                    time.sleep(5)

except KeyboardInterrupt:
    log.info('Received keyboard interrupt; quitting')
    gdx.stop()
    gdx.close()

DB.commit()
DB.close()

