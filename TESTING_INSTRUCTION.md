# 📋 ІНСТРУКЦІЯ З ДИНАМІЧНОГО ТЕСТУВАННЯ АРХІТЕКТУРИ

## Зміст
1. [Backend Testing (PyTest)](#1-backend-testing-pytest)
2. [Frontend Testing (Vitest)](#2-frontend-testing-vitest)
3. [API Testing (Postman)](#3-api-testing-postman)
4. [Load Testing (альтернативи JMeter)](#4-load-testing)
5. [Звіт про результати](#5-звіт-про-результати)

---

## 1. Backend Testing (PyTest)

### 📦 Встановлення залежностей

```bash
cd back
pip install -r requirements_test.txt
```

### ▶️ Запуск тестів

**Простий запуск:**
```bash
pytest test_server.py -v
pytest test_serial_reader.py -v
```

**Запуск всіх тестів:**
```bash
pytest -v
```

**З детальною інформацією:**
```bash
pytest -v --tb=short
```

**З покриттям коду:**
```bash
pytest --cov=server --cov=serial_reader --cov-report=html --cov-report=term
```

**Генерація JSON звіту:**
```bash
pytest --json-report --json-report-file=test_results.json
```

### 📊 Перегляд результатів

- Терміналі: відразу після запуску
- HTML покриття: `back/htmlcov/index.html` (відкрити у браузері)
- JSON звіт: `back/test_results.json`

---

## 2. Frontend Testing (Vitest)

### 📦 Встановлення залежностей

```bash
cd web/dashboard
npm install --save-dev vitest @vitest/ui jsdom @testing-library/react @testing-library/jest-dom
```

### ▶️ Додати scripts в package.json

Відкрийте `web/dashboard/package.json` і додайте:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "preview": "vite preview",
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:coverage": "vitest --coverage"
}
```

### ▶️ Запуск тестів

**Простий запуск:**
```bash
npm test
```

**Інтерактивний UI:**
```bash
npm run test:ui
```

**З покриттям коду:**
```bash
npm run test:coverage
```

**Один раз (CI режим):**
```bash
npm test -- --run
```

### 📊 Перегляд результатів

- Терміналі: відразу після запуску
- UI: відкриється браузер автоматично при `npm run test:ui`
- HTML покриття: `web/dashboard/coverage/index.html`

---

## 3. API Testing (Postman)

### 📥 Імпорт колекції

1. Відкрийте Postman
2. File → Import
3. Виберіть файл `back/postman_collection.json`
4. Натисніть Import

### ⚙️ Налаштування

**Відключення SSL перевірки (для локального тестування):**
- Settings (⚙️) → General → SSL certificate verification → OFF

**Налаштування змінних (опціонально):**
- Створіть Environment
- Додайте змінну: `base_url` = `https://127.0.0.1:8443`

### ▶️ Запуск тестів

**Окремий запит:**
- Виберіть запит
- Натисніть Send
- Перегляньте результати у вкладці "Test Results"

**Запуск всієї колекції:**
1. Клікніть правою кнопкою на колекцію "NFC Payments API - Dynamic Testing"
2. Виберіть "Run collection"
3. Налаштуйте параметри (iterations, delay)
4. Натисніть "Run NFC Payments API..."

**Через Newman (CLI):**
```bash
# Встановлення Newman
npm install -g newman

# Запуск колекції
newman run back/postman_collection.json --insecure

# З HTML звітом
newman run back/postman_collection.json --insecure --reporters cli,html --reporter-html-export newman-report.html
```

### 📊 Перегляд результатів

- В Postman: вкладка "Test Results"
- Newman HTML: `newman-report.html`
- Newman JSON: додайте `--reporters json --reporter-json-export results.json`

---

## 4. Load Testing

### Варіант A: Locust (рекомендовано для Python проектів)

**Встановлення:**
```bash
pip install locust
```

**Створення тестового файлу `locustfile.py`:**
```python
from locust import HttpUser, task, between

class NFCApiUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_transactions(self):
        self.client.get("/transactions?limit=50", verify=False)
    
    @task(2)
    def get_stats(self):
        self.client.get("/stats?hours=24", verify=False)
    
    @task(1)
    def create_transaction(self):
        self.client.post("/transactions", json={
            "uid": "LOADTEST",
            "status": "GRANTED"
        }, verify=False)
```

**Запуск:**
```bash
locust -f locustfile.py --host=https://127.0.0.1:8443 --users 10 --spawn-rate 2 --run-time 60s --headless --html load-test-report.html
```

**Параметри:**
- `--users 10` - 10 одночасних користувачів
- `--spawn-rate 2` - додавати по 2 користувачі за секунду
- `--run-time 60s` - тривалість тесту 60 секунд
- `--headless` - без UI (для автоматизації)

### Варіант B: Apache Bench (ab)

**Для Windows:**
```bash
# Якщо встановлено Apache
C:\Apache24\bin\ab.exe -n 1000 -c 10 https://127.0.0.1:8443/health

# -n 1000 = 1000 запитів
# -c 10 = 10 одночасних з'єднань
```

### Варіант C: Artillery

**Встановлення:**
```bash
npm install -g artillery
```

**Створення конфігурації `artillery.yml`:**
```yaml
config:
  target: "https://127.0.0.1:8443"
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 120
      arrivalRate: 10
      name: "Sustained load"
  tls:
    rejectUnauthorized: false

scenarios:
  - name: "API Load Test"
    flow:
      - get:
          url: "/health"
      - get:
          url: "/transactions?limit=50"
      - get:
          url: "/stats?hours=24"
      - post:
          url: "/transactions"
          json:
            uid: "ARTILLERY_TEST"
            status: "GRANTED"
```

**Запуск:**
```bash
artillery run artillery.yml --output report.json
artillery report report.json --output report.html
```

---

## 5. Звіт про результати

### 📋 Шаблон таблиці результатів

Створіть файл `TEST_RESULTS.md` з такою структурою:

```markdown
# Звіт про динамічне тестування архітектури

**Дата:** [Ваша дата]
**Виконав:** [Ваше ім'я]
**Версія системи:** 1.0

---

## 1. Backend Unit Tests (PyTest)

| № | Назва тесту | Модуль | Результат | Час виконання | Коментар |
|---|------------|--------|-----------|---------------|----------|
| 1 | test_health_check_success | test_server.py | ✅ PASS | 0.05s | - |
| 2 | test_create_transaction_granted | test_server.py | ✅ PASS | 0.12s | - |
| 3 | test_create_transaction_denied | test_server.py | ✅ PASS | 0.11s | - |
| 4 | test_create_transaction_empty_uid | test_server.py | ✅ PASS | 0.08s | - |
| 5 | test_list_transactions_default | test_server.py | ✅ PASS | 0.15s | - |
| 6 | test_post_transaction_success | test_serial_reader.py | ✅ PASS | 0.03s | - |
| ... | ... | ... | ... | ... | ... |

**Загальна статистика:**
- Всього тестів: [X]
- Успішних: [X]
- Помилкових: [X]
- Покриття коду: [X]%
- Загальний час: [X]s

---

## 2. Frontend Tests (Vitest)

| № | Назва тесту | Модуль | Результат | Час виконання | Коментар |
|---|------------|--------|-----------|---------------|----------|
| 1 | should fetch transactions successfully | api.test.ts | ✅ PASS | 0.02s | - |
| 2 | should throw error on failed fetch | api.test.ts | ✅ PASS | 0.01s | - |
| 3 | should fetch stats successfully | api.test.ts | ✅ PASS | 0.02s | - |
| ... | ... | ... | ... | ... | ... |

**Загальна статистика:**
- Всього тестів: [X]
- Успішних: [X]
- Помилкових: [X]
- Покриття коду: [X]%
- Загальний час: [X]s

---

## 3. API Integration Tests (Postman)

| № | Назва тесту | Endpoint | Метод | Результат | Час відповіді | Коментар |
|---|------------|----------|-------|-----------|---------------|----------|
| 1 | Health Check | /health | GET | ✅ PASS | 45ms | - |
| 2 | Create Transaction - GRANTED | /transactions | POST | ✅ PASS | 123ms | - |
| 3 | Create Transaction - DENIED | /transactions | POST | ✅ PASS | 118ms | - |
| 4 | Create Transaction - Invalid Status | /transactions | POST | ✅ PASS | 67ms | Валідація працює |
| 5 | List Transactions - Default | /transactions | GET | ✅ PASS | 234ms | - |
| 6 | Get Stats - Default (24h) | /stats | GET | ✅ PASS | 456ms | - |
| ... | ... | ... | ... | ... | ... | ... |

**Загальна статистика:**
- Всього тестів: [X]
- Успішних: [X]
- Помилкових: [X]
- Середній час відповіді: [X]ms
- Мінімальний час: [X]ms
- Максимальний час: [X]ms

---

## 4. Load Testing Results

**Інструмент:** [Locust/Artillery/ab]
**Конфігурація:**
- Кількість користувачів: [X]
- Тривалість тесту: [X] секунд
- Spawn rate: [X] users/s

### Результати:

| Метрика | Значення |
|---------|----------|
| Всього запитів | [X] |
| Успішних запитів | [X] |
| Помилкових запитів | [X] |
| Requests per second (RPS) | [X] |
| Середній час відповіді | [X]ms |
| Медіана часу відповіді | [X]ms |
| 95 перцентиль | [X]ms |
| 99 перцентиль | [X]ms |
| Мінімальний час | [X]ms |
| Максимальний час | [X]ms |

### Детальна статистика по endpoint:

| Endpoint | Запитів | Успішно | Помилок | Avg (ms) | Min (ms) | Max (ms) |
|----------|---------|---------|---------|----------|----------|----------|
| GET /health | [X] | [X] | [X] | [X] | [X] | [X] |
| GET /transactions | [X] | [X] | [X] | [X] | [X] | [X] |
| POST /transactions | [X] | [X] | [X] | [X] | [X] | [X] |
| GET /stats | [X] | [X] | [X] | [X] | [X] | [X] |

---

## 5. Загальні висновки

### Виявлені проблеми:
1. [Опис проблеми 1]
2. [Опис проблеми 2]
...

### Переваги системи:
1. [Перевага 1]
2. [Перевага 2]
...

### Рекомендації:
1. [Рекомендація 1]
2. [Рекомендація 2]
...

### Загальна оцінка якості:
- **Функціональність:** [X]/10
- **Продуктивність:** [X]/10
- **Надійність:** [X]/10
- **Масштабованість:** [X]/10

**Висновок:** [Ваш загальний висновок про якість системи]
```

---

## 📝 Покрокова інструкція виконання

### Крок 1: Підготовка середовища

```bash
# Backend
cd back
pip install -r requirements_test.txt

# Frontend
cd ../web/dashboard
npm install --save-dev vitest @vitest/ui jsdom

# Load testing (вибрати один варіант)
pip install locust
# або
npm install -g artillery
```

### Крок 2: Запуск сервера

**Термінал 1 - Backend:**
```bash
cd back
uvicorn server:app --host 127.0.0.1 --port 8443 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

**Термінал 2 - Frontend:**
```bash
cd web/dashboard
npm run dev
```

### Крок 3: Виконання тестів

**Термінал 3 - Backend тести:**
```bash
cd back
pytest -v --cov=server --cov=serial_reader --cov-report=html
```

**Термінал 4 - Frontend тести:**
```bash
cd web/dashboard
npm test -- --run --coverage
```

**Postman:**
- Відкрити Postman
- Імпортувати `back/postman_collection.json`
- Запустити колекцію (Run collection)
- Експортувати результати

**Load testing:**
```bash
# Locust
locust -f locustfile.py --host=https://127.0.0.1:8443 --users 10 --spawn-rate 2 --run-time 60s --headless --html load-report.html

# або Artillery
artillery run artillery.yml --output artillery-report.json
artillery report artillery-report.json --output artillery-report.html
```

### Крок 4: Збір результатів

1. **PyTest результати:**
   - Консольний вивід (скріншот)
   - `back/htmlcov/index.html` (скріншот)

2. **Vitest результати:**
   - Консольний вивід (скріншот)
   - `web/dashboard/coverage/index.html` (скріншот)

3. **Postman результати:**
   - Test Results (скріншот)
   - Експорт результатів у JSON

4. **Load testing:**
   - HTML звіти (скріншоти)
   - Ключові метрики

### Крок 5: Заповнення звіту

1. Скопіюйте шаблон з розділу "Звіт про результати"
2. Заповніть таблиці фактичними даними з тестів
3. Додайте скріншоти
4. Напишіть висновки та рекомендації

---

## 🛠️ Troubleshooting

### Проблема: pytest не знаходить модулі

**Рішення:**
```bash
cd back
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest -v
```

### Проблема: SSL помилки в Postman/Newman

**Рішення:**
- В Postman: Settings → SSL verification → OFF
- В Newman: додайте `--insecure` флаг

### Проблема: Vitest не запускається

**Рішення:**
```bash
cd web/dashboard
npm install --save-dev @vitest/ui jsdom
```

### Проблема: MongoDB connection error

**Рішення:**
- Перевірте підключення до інтернету
- Перевірте MongoDB URI в `server.py`
- Використайте mock MongoDB (mongomock) для тестів

---

## 📚 Додаткові ресурси

- [PyTest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Postman Learning Center](https://learning.postman.com/)
- [Locust Documentation](https://docs.locust.io/)
- [Artillery Documentation](https://www.artillery.io/docs)

---

**Успіхів у тестуванні! 🚀**
```


