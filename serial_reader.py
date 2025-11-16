import serial
import time
import json
import requests

# ================== Налаштування ==================
COM_PORT = 'COM4'         # порт Arduino (віртуальна пара: Arduino на COM3, Python на COM4)
BAUD_RATE = 9600
TIMEOUT = 1               # секунди таймауту для serial
API_URL = "https://127.0.0.1:8443/transactions"  # Ендпойнт для запису в БД через HTTPS (Uvicorn TLS)
DEBUG = True  # Увімкнути для детальних логів парсингу
ALLOWED_UIDS = ["A1B2C3D4", "CAFEBABE"]  # Локальний список дозволених UID, якщо Arduino шле лише UID

# HTTPS валідація сертифіката:
# - Вкажіть шлях до вашого self-signed сертифіката (наприклад, "cert.pem"), щоб requests довіряв йому
# - Якщо CERT_PATH = None, буде використано системні довірені сертифікати
# - Якщо CERT_PATH = False, перевірка вимикається (НЕ рекомендовано)
CERT_PATH = "cert.pem"
REQUESTS_VERIFY = CERT_PATH if CERT_PATH is not None else True

# Валідація відбувається на Arduino. Python лише приймає JSON/рядки і відправляє POST на сервер.

# Відкриваємо COM-порт (фіксований COM-порт вашої віртуальної пари)
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=TIMEOUT)
time.sleep(2.5)  # Дати час на ініціалізацію/автоскидання
print("Listening on", COM_PORT)


def post_transaction(payload: dict) -> None:
    """Надсилаємо транзакцію на сервер через HTTP(S) POST"""
    try:
        if DEBUG:
            print("[POST] ->", payload)
        resp = requests.post(API_URL, json=payload, timeout=5, verify=REQUESTS_VERIFY)
        if resp.status_code >= 200 and resp.status_code < 300:
            print("[POST] OK", payload)
        else:
            print(f"[POST] Failed {resp.status_code}: {resp.text}")
    except Exception as e:
        print("[POST] Error:", e)


def parse_and_forward_line(line: str) -> None:
    """Парсимо рядок з Arduino і відправляємо на сервер"""
    global _json_accum, _json_open, _pending_uid, _pending_uid_ts

    # Ігнорувати шумові логи
    if line.startswith("Received UID:") or line.startswith("Access "):
        if DEBUG:
            print("[IGN] noise:", line)
        return

    # Підтримка мульти-рядкового JSON: накопичуємо до '}' (спрощено)
    if _json_open:
        _json_accum += line
        if DEBUG:
            print("[JSON] append:", line)
        if line.endswith("}"):
            data_str = _json_accum
            _json_accum = ""
            _json_open = False
            try:
                data = json.loads(data_str)
                uid = str(data.get("uid", "")).strip()
                status = str(data.get("status", "")).strip().upper()
                ts = data.get("timestamp")
                if ts is None:
                    ts = time.time()
                if DEBUG:
                    print("[JSON] complete:", data_str)
                post_transaction({"uid": uid, "status": status, "timestamp": float(ts)})
                return
            except Exception as e:
                print("[PARSE] JSON-accum error:", e, "raw:", data_str)
                return
        else:
            return

    # Старт мульти-рядкового JSON
    if line.startswith("{") and not line.endswith("}"):
        _json_open = True
        _json_accum = line
        if DEBUG:
            print("[JSON] start:", line)
        return

    # Формат 1: JSON {"uid":"...", "status":"GRANTED|DENIED", "timestamp": 1731700000} або {"date":"ISO8601"}
    if line.startswith("{") and line.endswith("}"):
        try:
            data = json.loads(line)
            uid = str(data.get("uid", "")).strip()
            status = str(data.get("status", "")).strip().upper()
            ts = data.get("timestamp")
            if ts is None:
                # Підтримка поля "date" (ISO8601), якщо воно є
                date_str = data.get("date") or data.get("datetime")
                if isinstance(date_str, str) and len(date_str) > 0:
                    try:
                        # Найпростіше: якщо це unix seconds as string
                        ts = float(date_str)
                    except Exception:
                        # Якщо це ISO8601, відправимо поточний час (спростимо)
                        ts = time.time()
                else:
                    ts = time.time()
            payload = {"uid": uid, "status": status, "timestamp": float(ts)}
            post_transaction(payload)
            return
        except Exception as e:
            print("[PARSE] JSON error:", e)
            # Падати не будемо — спробуємо інші формати

    # Формат 2: "TXN:UID:GRANTED|DENIED"
    if line.startswith("TXN:"):
        parts = line.split(":")
        if len(parts) == 3:
            _, uid, status = parts
            payload = {
                "uid": uid.strip(),
                "status": status.strip().upper(),
                "timestamp": time.time()
            }
            post_transaction(payload)
            return
        else:
            print("Invalid TXN format:", line)
            return

    # Формат 3: «сирий» UID (8 hex)
    if len(line) == 8 and all(ch in "0123456789abcdefABCDEF" for ch in line):
        # Якщо Arduino не шле статус, вирішуємо локально
        status = "GRANTED" if line.upper() in {u.upper() for u in ALLOWED_UIDS} else "DENIED"
        if DEBUG:
            print("[LOCAL] UID only ->", line, status)
        post_transaction({"uid": line, "status": status, "timestamp": time.time()})
        return

    # Якщо приходить рядок зі статусом окремо — ігноруємо, бо статус вже визначаємо локально
    if line.upper() in ("GRANTED", "DENIED"):
        return

    # Інші службові рядки можна ігнорувати
    if line in ("SYNC:OK", "REQSYNC") or line.startswith("LIST:") or line == "LIST:END" or line.startswith("Received UID:"):
        return

    # Невідомий рядок — вважаємо як UID з DENIED (за вимогою)
    if line:
        if DEBUG:
            print("[AUTO] Unknown -> DENIED:", line)
        post_transaction({
            "uid": line,
            "status": "DENIED",
            "timestamp": time.time()
        })
        return

    return


# ================== Робота без синхронізації ==================
# Жодного SYNC: Arduino сам вирішує допуск. Python лише рісеє і форвардить.

# ================== Основний цикл ==================
line_buffer = ""
_json_accum = ""
_json_open = False
_pending_uid = None
_pending_uid_ts = None

while True:
    try:
        # Читаємо байти з Arduino
        if ser.in_waiting > 0:
            c = ser.read().decode('utf-8', errors='ignore')
            if c in '\r\n':
                if line_buffer:
                    line = line_buffer.strip()
                    line_buffer = ""
                    if DEBUG:
                        print("[SER] RX:", repr(line))
                    parse_and_forward_line(line)
            else:
                line_buffer += c

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
