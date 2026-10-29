import os
import sys
import io
import M5
from M5 import *
import m5ui
import lvgl as lv
import time
import math
import random
import network
import requests

# ---------- Configuración ----------
WIFI_SSID = "B14-ALUMNOS"
WIFI_PASSWORD = "56#?qwal"
URL_ENDPOINT = "https://jbc-app-daw-default-rtdb.europe-west1.firebasedatabase.app/datos.json"

INTERVALO_MS = 30000          # 30 segundos entre envíos
RECONNECT_MS = 5000

CENTRO_LAT = 38.98626
CENTRO_LON = -3.92742
RADIO_GIRO = 0.005

# ---------- Estado ----------
page0 = None
lbl_titulo = None
lbl_lat = None
lbl_lon = None
lbl_vel = None
lbl_volt = None
lbl_estado = None
lbl_http = None
lbl_wifi = None
lbl_cuenta = None
led0 = None
btn_parar = None
btn_reanudar = None
wlan = None

envio_activo = True
angulo = 0.0
last_send = 0
last_reconnect = 0
first_send = True
envios_ok = 0
cache = {}   # para refrescar etiquetas solo cuando cambian


def set_lbl(key, lbl, txt):
    """Actualiza una etiqueta solo si el texto cambió (evita parpadeo)."""
    if cache.get(key) != txt:
        lbl.set_text(txt)
        cache[key] = txt


def btn_parar_cb(event_struct):
    global envio_activo
    envio_activo = False
    led0.off()
    set_lbl("estado", lbl_estado, "Estado: EN PAUSA")


def btn_reanudar_cb(event_struct):
    global envio_activo
    envio_activo = True
    set_lbl("estado", lbl_estado, "Estado: ENVIANDO")


def setup():
    global page0, lbl_titulo, lbl_lat, lbl_lon, lbl_vel, lbl_volt
    global lbl_estado, lbl_http, lbl_wifi, lbl_cuenta, led0
    global btn_parar, btn_reanudar, wlan, last_reconnect

    M5.begin()
    Widgets.setRotation(1)
    m5ui.init()

    page0 = m5ui.M5Page(bg_c=0xffffff)
    f = lv.font_montserrat_14

    lbl_titulo = m5ui.M5Label(text="Telemetria coche electrico", x=10, y=6, font=f, text_c=0x1565c0, parent=page0)
    led0 = m5ui.M5LED(x=285, y=6, size=20, color=0x00ff00, on=False, parent=page0)

    lbl_lat = m5ui.M5Label(text="Lat: --", x=10, y=34, font=f, text_c=0x000000, parent=page0)
    lbl_lon = m5ui.M5Label(text="Lon: --", x=10, y=56, font=f, text_c=0x000000, parent=page0)
    lbl_vel = m5ui.M5Label(text="Velocidad: -- km/h", x=10, y=78, font=f, text_c=0x000000, parent=page0)
    lbl_volt = m5ui.M5Label(text="Voltaje: -- V", x=10, y=100, font=f, text_c=0x000000, parent=page0)

    lbl_estado = m5ui.M5Label(text="Estado: ENVIANDO", x=10, y=126, font=f, text_c=0x212121, parent=page0)
    lbl_http = m5ui.M5Label(text="HTTP: --  (envios OK: 0)", x=10, y=146, font=f, text_c=0x212121, parent=page0)
    lbl_wifi = m5ui.M5Label(text="WiFi: conectando...", x=10, y=166, font=f, text_c=0x212121, parent=page0)
    lbl_cuenta = m5ui.M5Label(text="Proximo envio: --", x=10, y=186, font=f, text_c=0x212121, parent=page0)

    btn_parar = m5ui.M5Button(text="Parar", x=10, y=208, w=145, h=28,
                              bg_c=0xd32f2f, text_c=0xffffff, font=f, parent=page0)
    btn_reanudar = m5ui.M5Button(text="Reanudar", x=165, y=208, w=145, h=28,
                                 bg_c=0x388e3c, text_c=0xffffff, font=f, parent=page0)
    btn_parar.add_event_cb(btn_parar_cb, lv.EVENT.CLICKED, None)
    btn_reanudar.add_event_cb(btn_reanudar_cb, lv.EVENT.CLICKED, None)

    page0.screen_load()

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    except Exception:
        pass
    last_reconnect = time.ticks_ms()


def enviar_telemetria():
    """Genera datos simulados, los muestra en pantalla y los envía a Firebase."""
    global angulo, envios_ok

    lat = CENTRO_LAT + RADIO_GIRO * math.sin(angulo)
    lon = CENTRO_LON + RADIO_GIRO * math.cos(angulo)
    angulo += 0.2
    if angulo >= 2 * math.pi:
        angulo = 0.0

    velocidad = random.randint(20, 45)            # km/h
    voltaje = random.randint(360, 420) / 10.0     # V

    # Mostrar en pantalla (en lugar del monitor serie)
    set_lbl("lat", lbl_lat, "Lat: {:.5f}".format(lat))
    set_lbl("lon", lbl_lon, "Lon: {:.5f}".format(lon))
    set_lbl("vel", lbl_vel, "Velocidad: {} km/h".format(velocidad))
    set_lbl("volt", lbl_volt, "Voltaje: {} V".format(voltaje))

    datos = {
        "latitud": lat,
        "longitud": lon,
        "velocidad_kmh": velocidad,
        "voltaje_v": voltaje,
        "timestamp": time.ticks_ms()
    }

    led0.on()
    try:
        res = requests.post(URL_ENDPOINT, json=datos)
        codigo = res.status_code
        res.close()
        if codigo == 200 or codigo == 201:
            envios_ok += 1
        set_lbl("http", lbl_http, "HTTP: {}  (envios OK: {})".format(codigo, envios_ok))
    except Exception:
        set_lbl("http", lbl_http, "HTTP: error de envio")
    led0.off()


def loop():
    global last_send, last_reconnect, first_send
    M5.update()
    now = time.ticks_ms()

    if wlan.isconnected():
        set_lbl("wifi", lbl_wifi, "WiFi: conectado")

        if envio_activo:
            set_lbl("estado", lbl_estado, "Estado: ENVIANDO")
            transcurrido = time.ticks_diff(now, last_send)

            if first_send or transcurrido >= INTERVALO_MS:
                first_send = False
                last_send = now
                enviar_telemetria()
            else:
                restante = (INTERVALO_MS - transcurrido) // 1000
                set_lbl("cuenta", lbl_cuenta, "Proximo envio: {} s".format(restante))
        else:
            set_lbl("estado", lbl_estado, "Estado: EN PAUSA")
            set_lbl("cuenta", lbl_cuenta, "Proximo envio: en pausa")
    else:
        set_lbl("wifi", lbl_wifi, "WiFi: buscando " + WIFI_SSID)
        if time.ticks_diff(now, last_reconnect) >= RECONNECT_MS:
            last_reconnect = now
            try:
                wlan.disconnect()
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            except Exception:
                pass

    time.sleep_ms(100)


if __name__ == '__main__':
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            m5ui.deinit()
            from utility import print_error_msg
            print_error_msg(e)
        except ImportError:
            print("Programa detenido.")