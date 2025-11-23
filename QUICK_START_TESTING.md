# ⚡ Швидка шпаргалка з динамічного тестування

## 🎯 Швидкий старт (копіюй та вставляй команди)

### 1️⃣ Підготовка середовища

```bash
# Backend
cd back
pip install -r requirements_test.txt
pip install locust

# Frontend  
cd ../web/dashboard
npm install --save-dev vitest @vitest/ui jsdom

# Newman (для CLI Postman)
npm install -g newman
```

### 2️⃣ Запуск серверів

**Термінал 1 - Backend Server:**
```bash
cd back
uvicorn server:app --host 127.0.0.1 --port 8443 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

**Термінал 2 - Frontend Dev Server (опціонально):**
```bash
cd web/dashboard
npm run dev
```

### 3️⃣ Запуск тестів

#### 📌 Backend Tests (PyTest)

```bash
cd back

# Простий запуск
pytest -v

# З покриттям коду
pytest -v --cov=server --cov=serial_reader --cov-report=html --cov-report=term

# Тільки server.py
pytest test_server.py -v

# Тільки serial_reader.py  
pytest test_serial_reader.py -v

# З детальним виводом при помилках
pytest -v --tb=long
```

**Результати:**
- Консоль: відразу
- HTML покриття: `back/htmlcov/index.html`

#### 📌 Frontend Tests (Vitest)

```bash
cd web/dashboard

# Простий запуск
npm test

# Один раз (CI режим)
npm test -- --run

# З покриттям
npm test -- --run --coverage

# Інтерактивний UI
npm run test:ui
```

**Результати:**
- Консоль: відразу
- HTML покриття: `web/dashboard/coverage/index.html`

#### 📌 API Tests (Postman)

**Через Postman UI:**
1. Відкрийте Postman
2. File → Import → `back/postman_collection.json`
3. Settings → SSL verification → OFF
4. Клік правою на колекцію → "Run collection"
5. Запустити

**Через Newman (CLI):**
```bash
# Простий запуск
newman run back/postman_collection.json --insecure

# З HTML звітом
newman run back/postman_collection.json --insecure \
  --reporters cli,html \
  --reporter-html-export postman-report.html

# З JSON звітом
newman run back/postman_collection.json --insecure \
  --reporters cli,json \
  --reporter-json-export postman-results.json
```

**Результати:**
- Консоль: відразу
- HTML: `postman-report.html`
- JSON: `postman-results.json`

#### 📌 Load Testing (Locust)

```bash
cd back

# Web UI режим (інтерактивно)
locust -f locustfile.py --host=https://127.0.0.1:8443
# Відкрийте http://localhost:8089

# Headless режим (автоматично)
locust -f locustfile.py \
  --host=https://127.0.0.1:8443 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --headless \
  --html load-report.html

# Швидкий тест (30 секунд, 20 користувачів)
locust -f locustfile.py \
  --host=https://127.0.0.1:8443 \
  --users 20 \
  --spawn-rate 4 \
  --run-time 30s \
  --headless \
  --html quick-load-test.html

# З CSV звітами
locust -f locustfile.py \
  --host=https://127.0.0.1:8443 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --csv=results \
  --html=results.html
```

**Результати:**
- Web UI: http://localhost:8089
- HTML: `load-report.html`
- CSV: `results_stats.csv`, `results_failures.csv`

#### 📌 Load Testing (Artillery - альтернатива)

```bash
cd back

# Встановлення
npm install -g artillery

# Запуск з конфігурацією
artillery run artillery.yml --output artillery-report.json

# Генерація HTML звіту
artillery report artillery-report.json --output artillery-report.html

# Швидкий тест
artillery quick --count 100 --num 10 https://127.0.0.1:8443/health
```

---

## 📊 Збір результатів для звіту

### Крок 1: Запустити всі тести

```bash
# Термінал 1: Backend tests
cd back
pytest -v --cov=server --cov=serial_reader --cov-report=html > pytest-output.txt

# Термінал 2: Frontend tests  
cd web/dashboard
npm test -- --run --coverage > vitest-output.txt

# Термінал 3: Postman tests
newman run back/postman_collection.json --insecure \
  --reporters cli,html,json \
  --reporter-html-export postman-report.html \
  --reporter-json-export postman-results.json

# Термінал 4: Load tests
cd back
locust -f locustfile.py \
  --host=https://127.0.0.1:8443 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --headless \
  --html load-report.html \
  --csv=load-results
```

### Крок 2: Зібрати файли результатів

```
Файли для звіту:
├── back/
│   ├── pytest-output.txt          # PyTest консольний вивід
│   ├── htmlcov/index.html         # PyTest покриття коду
│   ├── load-report.html           # Locust звіт
│   ├── load-results_stats.csv     # Locust детальна статистика
│   └── postman-report.html        # Postman звіт
└── web/dashboard/
    ├── vitest-output.txt          # Vitest консольний вивід
    └── coverage/index.html        # Vitest покриття коду
```

### Крок 3: Зробити скріншоти

📸 **Необхідні скріншоти:**
1. PyTest консольний вивід
2. PyTest HTML coverage (back/htmlcov/index.html)
3. Vitest консольний вивід
4. Vitest coverage (web/dashboard/coverage/index.html)
5. Postman Test Runner результати
6. Locust dashboard або HTML звіт
7. Locust графіки (response time, RPS, users)

### Крок 4: Заповнити шаблон

1. Відкрити `TEST_RESULTS_TEMPLATE.md`
2. Скопіювати у новий файл `TEST_RESULTS.md`
3. Заповнити таблиці даними з тестів
4. Вставити скріншоти
5. Написати висновки

---

## 🔍 Аналіз результатів

### PyTest - що дивитись:

```bash
# Консоль показує:
collected X items                           # Кількість тестів
test_server.py::TestName::test_name PASSED # Результат кожного тесту
====== X passed in X.XXs ======             # Підсумок

# Coverage показує:
Name            Stmts   Miss  Cover
-----------------------------------
server.py         150     10    93%
serial_reader.py  120     15    88%
-----------------------------------
TOTAL            270     25    91%
```

**Заповніть у таблицю:**
- Назву тесту
- PASS/FAIL
- Час виконання
- Відсоток покриття

### Vitest - що дивитись:

```bash
# Консоль показує:
✓ src/api.test.ts (6)                    # Файл та к-сть тестів
  ✓ should fetch transactions (23ms)     # Тест та час
  
Test Files  1 passed (1)
Tests       6 passed (6)
```

### Postman/Newman - що дивитись:

```bash
# Newman показує:
→ Test Name
  GET https://127.0.0.1:8443/endpoint [200 OK, 234B, 123ms]
  ✓ Status code is 200
  ✓ Response has required fields
  
┌─────────────────────────┬────────┬────────┐
│                         │ executed│ failed │
├─────────────────────────┼────────┼────────┤
│              iterations │      1 │      0 │
├─────────────────────────┼────────┼────────┤
│                requests │     12 │      0 │
├─────────────────────────┼────────┼────────┤
│            test-scripts │     12 │      0 │
├─────────────────────────┼────────┼────────┤
│      prerequest-scripts │      0 │      0 │
├─────────────────────────┼────────┼────────┤
│              assertions │     29 │      0 │
└─────────────────────────┴────────┴────────┘
```

### Locust - що дивитись:

```bash
# Консоль або HTML показує:
Name                 # Requests    # Fails   Avg (ms)  Min   Max   Median  RPS
GET /health              2341         0         23      12    156    20     19.5
POST /transactions       5678        13         98      34   1234    87     47.3

Aggregated:
Total requests: 15432
Failures: 34 (0.22%)
RPS: 128.6
Average response time: 87ms
```

---

## 📝 Чеклист виконання

- [ ] Встановлено всі залежності (pytest, vitest, locust)
- [ ] Запущено backend сервер
- [ ] Виконано PyTest backend тести
- [ ] Виконано Vitest frontend тести
- [ ] Виконано Postman API тести
- [ ] Виконано Load testing (Locust/Artillery)
- [ ] Зроблено всі необхідні скріншоти
- [ ] Зібрано всі HTML звіти
- [ ] Заповнено таблиці у TEST_RESULTS.md
- [ ] Написано висновки та рекомендації
- [ ] Перевірено орфографію та форматування

---

## 🛠️ Troubleshooting

### Проблема: ModuleNotFoundError

```bash
# Рішення:
cd back
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%          # Windows CMD
$env:PYTHONPATH += ";$(pwd)"              # Windows PowerShell
```

### Проблема: SSL Errors

```bash
# Postman: Settings → SSL verification → OFF
# Newman: додайте --insecure
# Python: requests.post(..., verify=False)
# Locust: вже налаштовано (insecure=True)
```

### Проблема: MongoDB Connection

```bash
# Для тестів можна використати mock:
pip install mongomock

# В тестах:
from mongomock import MongoClient
```

### Проблема: Port Already in Use

```bash
# Windows:
netstat -ano | findstr :8443
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8443 | xargs kill
```

### Проблема: Vitest не знаходить modules

```bash
cd web/dashboard
npm install --save-dev @vitest/ui jsdom @testing-library/react
```

---

## 🎓 Додаткові команди

### Перевірка quality коду

```bash
# Backend - pylint
cd back
pylint *.py

# Frontend - eslint
cd web/dashboard
npm run lint
```

### Генерація різних форматів звітів

```bash
# PyTest - різні формати
pytest --html=report.html --self-contained-html
pytest --json-report --json-report-file=report.json
pytest --cov=. --cov-report=xml --cov-report=term

# Newman - різні формати
newman run collection.json --insecure \
  --reporters cli,html,json,junit \
  --reporter-html-export report.html \
  --reporter-json-export report.json \
  --reporter-junit-export report.xml
```

### Continuous testing (watch mode)

```bash
# PyTest watch
pip install pytest-watch
ptw -- -v

# Vitest watch (за замовчуванням)
npm test
```

---

## 📚 Корисні посилання

- [PyTest Docs](https://docs.pytest.org/)
- [Vitest Docs](https://vitest.dev/)
- [Newman Docs](https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/)
- [Locust Docs](https://docs.locust.io/)
- [Artillery Docs](https://www.artillery.io/docs)

---

**Готово! Тепер просто копіюйте команди та виконуйте! 🚀**

