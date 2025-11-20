#include <LiquidCrystal.h>

LiquidCrystal lcd(2, 3, 4, 5, 6, 7);

const int greenLedPin = 12;
const int redLedPin = 13;

#define MAX_UIDS 20
#define UID_LEN 8

// Зберігаємо дозволені UID в RAM як масив рядків (String)
String allowedUIDs[MAX_UIDS];
int allowedCount = 0;

void setup() {
  Serial.begin(9600);
  pinMode(greenLedPin, OUTPUT);
  pinMode(redLedPin, OUTPUT);
  lcd.begin(16, 2);
  lcd.print("Scan card...");
  Serial.println("Please scan your RFID TAG");

  // Початкові значення (можна залишити пустим)
  addAllowed("A1B2C3D4");
  addAllowed("CAFEBABE");
}

bool isAllowed(const String &uid) {
  for (int i = 0; i < allowedCount; ++i) {
    if (allowedUIDs[i] == uid) return true;
  }
  return false;
}

void indicateGranted() {
  digitalWrite(redLedPin, LOW);
  digitalWrite(greenLedPin, HIGH);
  delay(800);
  digitalWrite(greenLedPin, LOW);
}

void indicateDenied() {
  digitalWrite(greenLedPin, LOW);
  for (int i = 0; i < 2; ++i) {
    digitalWrite(redLedPin, HIGH);
    delay(150);
    digitalWrite(redLedPin, LOW);
    delay(100);
  }
}

void showUID(const String &uid) {
  // Інформаційні повідомлення на екран/консоль
  Serial.print("Received UID: ");
  Serial.println(uid);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("UID: ");
  lcd.print(uid);

  lcd.setCursor(0, 1);

  // Валідація тільки на Arduino
  bool ok = isAllowed(uid);
  const char* statusStr = ok ? "GRANTED" : "DENIED";

  if (ok) {
    lcd.print("Access: GRANTED");
    Serial.println("Access granted");
    indicateGranted();
  } else {
    lcd.print("Access: DENIED");
    Serial.println("Access denied");
    indicateDenied();
  }

  Serial.print("TXN:");
  Serial.print(uid);
  Serial.print(":");
  Serial.println(statusStr);
}

void clearAllowed() {
  allowedCount = 0;
}

void addAllowed(const String &uid) {
  if (allowedCount >= MAX_UIDS) return;
  // уникаємо дублікатів
  for (int i = 0; i < allowedCount; ++i) {
    if (allowedUIDs[i] == uid) return;
  }
  allowedUIDs[allowedCount++] = uid;
}

// Розбір SYNC:UID1,UID2,... — очищаємо поточний список і додаємо новий
void handleSync(const String &payload) {
  clearAllowed();
  int start = 0;
  int len = payload.length();
  while (start < len) {
    int comma = payload.indexOf(',', start);
    if (comma == -1) comma = len;
    String uid = payload.substring(start, comma);
    uid.trim();
    if (uid.length() > 0) {
      addAllowed(uid);
    }
    start = comma + 1;
  }
  Serial.println("SYNC:OK");
}

// Якщо Arduino хоче запросити список — відправляє REQSYNC, Python має відповісти
// Можемо також підтримати додавання одного UID: ADD:UID
void handleCommand(const String &cmd) {
  if (cmd.startsWith("SYNC:")) {
    String payload = cmd.substring(5); // після "SYNC:"
    handleSync(payload);
  } else if (cmd.startsWith("ADD:")) {
    String uid = cmd.substring(4);
    uid.trim();
    if (uid.length() > 0) addAllowed(uid);
    Serial.println("ADD:OK");
  } else if (cmd == "REQSYNC") {
    // Arduino просить Python надіслати SYNC — просто повідомляємо готовність
    Serial.println("REQSYNC");
  } else if (cmd == "LIST") {
    // Відправляємо локальний список назад
    for (int i = 0; i < allowedCount; ++i) {
      Serial.print("LIST:");
      Serial.println(allowedUIDs[i]);
    }
    Serial.println("LIST:END");
  } else {
    // Нічого
  }
}

void loop() {
  static String line = "";
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\r' || c == '\n') {
      if (line.length() > 0) {
        line.trim();
        // Команди мають префікси
        if (line.startsWith("SYNC:") || line.startsWith("ADD:") || line == "REQSYNC" || line == "LIST") {
          handleCommand(line);
        } else {
          // Якщо це UID (8 символів) або інший формат - просто показуємо
          showUID(line);
        }
        line = "";
      }
    } else {
      line += c;
      // обмеження довжини
      if (line.length() > 64) line = line.substring(line.length() - 64);
    }
  }
}


