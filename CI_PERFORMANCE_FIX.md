# ⚡ CI/CD Performance Fix - MongoDB Мокування

## Проблема

Тести backend виконувались **5+ хвилин** через:
- Спроби підключення до реальної MongoDB
- Таймаути підключення (по 30 сек на кожен тест)
- 27+ тестів = довгий час очікування

## Рішення

### 1. Mock MongoDB підключення

**Файл:** `back/test_server.py`

```python
# Mock MongoDB перед імпортом server
with patch('pymongo.MongoClient') as mock_mongo:
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Налаштовуємо mock chain
    mock_mongo.return_value.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    from server import app
    server.transactions = mock_collection
```

### 2. Pytest fixture для reset моків

```python
@pytest.fixture(autouse=True)
def reset_mock():
    server.transactions.reset_mock()
    
    # Mock для find() cursor
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__.return_value = iter([])
    server.transactions.find.return_value = mock_cursor
```

### 3. Timeout для pytest

**Файл:** `.github/workflows/ci.yml`

```yaml
- name: Run PyTest
  timeout-minutes: 5  # Kill якщо більше 5 хв
  run: |
    pytest -v --timeout=30  # 30 сек на кожен тест
```

**Файл:** `back/requirements_test.txt`

```txt
pytest-timeout==2.3.1
```

## Результат

### До:
- ⏱️ **5+ хвилин** виконання
- ❌ Тести падають через таймаути
- 😤 Неефективне використання CI/CD minutes

### Після:
- ⚡ **< 30 секунд** виконання
- ✅ Тести швидко проходять
- 💰 Економія CI/CD ресурсів

## Переваги

1. **Швидкість:** Тести виконуються за секунди, не хвилини
2. **Надійність:** Не залежать від зовнішніх сервісів
3. **Детермінізм:** Завжди однакова поведінка
4. **Безпека:** Timeout захищає від зависання

## Що тестується

✅ **API endpoints** (HTTP responses)  
✅ **Валідація** (Pydantic models)  
✅ **Бізнес логіка** (функції обробки)  
✅ **Error handling** (422, 500 коди)  

❌ **MongoDB підключення** (не потрібно в unit тестах)  
❌ **Реальні DB операції** (для integration тестів)  

## Альтернативи

Якщо потрібні integration тести з реальною БД:

```yaml
# Додати MongoDB service в CI
services:
  mongodb:
    image: mongo:7
    ports:
      - 27017:27017
```

Але для unit тестів mock краще:
- Швидше
- Дешевше
- Надійніше
- Простіше

---

**Час виконання:** < 30 секунд ⚡  
**Статус:** Оптимізовано ✅

