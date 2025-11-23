"""
Динамічне тестування FastAPI сервера
Запуск: pytest test_server.py -v --tb=short
"""
import time
import pytest
from fastapi.testclient import TestClient
from server import app, TransactionIn

client = TestClient(app)


class TestHealthEndpoint:
    """Тести для health check endpoint"""
    
    def test_health_check_success(self):
        """Тест перевірки здоров'я сервісу"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


class TestTransactionsPost:
    """Тести для POST /transactions"""
    
    def test_create_transaction_granted(self):
        """Тест створення транзакції зі статусом GRANTED"""
        payload = {
            "uid": "A1B2C3D4",
            "status": "GRANTED",
            "timestamp": time.time()
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "id" in data
        assert data["id"] is not None
    
    def test_create_transaction_denied(self):
        """Тест створення транзакції зі статусом DENIED"""
        payload = {
            "uid": "DEADBEEF",
            "status": "DENIED",
            "timestamp": time.time()
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
    
    def test_create_transaction_lowercase_status(self):
        """Тест створення транзакції з lowercase статусом"""
        payload = {
            "uid": "TEST1234",
            "status": "granted",
            "timestamp": time.time()
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
    
    def test_create_transaction_without_timestamp(self):
        """Тест створення транзакції без timestamp (має використати поточний час)"""
        payload = {
            "uid": "NOTIMESTAMP",
            "status": "GRANTED"
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
    
    def test_create_transaction_empty_uid(self):
        """Тест створення транзакції з пустим UID (має бути помилка валідації)"""
        payload = {
            "uid": "",
            "status": "GRANTED"
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_create_transaction_invalid_status(self):
        """Тест створення транзакції з невалідним статусом"""
        payload = {
            "uid": "TEST5678",
            "status": "INVALID"
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_create_transaction_missing_required_fields(self):
        """Тест створення транзакції без обов'язкових полів"""
        payload = {}
        response = client.post("/transactions", json=payload)
        assert response.status_code == 422  # Validation error


class TestTransactionsGet:
    """Тести для GET /transactions"""
    
    def test_list_transactions_default(self):
        """Тест отримання списку транзакцій з дефолтними параметрами"""
        response = client.get("/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_transactions_with_limit(self):
        """Тест отримання списку транзакцій з обмеженням"""
        response = client.get("/transactions?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_list_transactions_with_skip(self):
        """Тест отримання списку транзакцій з пропуском"""
        response = client.get("/transactions?skip=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_transactions_filter_by_status_granted(self):
        """Тест фільтрації транзакцій за статусом GRANTED"""
        response = client.get("/transactions?status=GRANTED")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for txn in data:
            assert txn["status"] == "GRANTED"
    
    def test_list_transactions_filter_by_status_denied(self):
        """Тест фільтрації транзакцій за статусом DENIED"""
        response = client.get("/transactions?status=DENIED")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for txn in data:
            assert txn["status"] == "DENIED"
    
    def test_list_transactions_filter_by_uid(self):
        """Тест фільтрації транзакцій за UID"""
        # Спочатку створимо транзакцію
        test_uid = "TESTUID123"
        payload = {"uid": test_uid, "status": "GRANTED"}
        client.post("/transactions", json=payload)
        
        # Тепер шукаємо її
        response = client.get(f"/transactions?uid={test_uid}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert data[0]["uid"] == test_uid
    
    def test_list_transactions_filter_by_since(self):
        """Тест фільтрації транзакцій за часом"""
        since_time = time.time() - 3600  # 1 година тому
        response = client.get(f"/transactions?since={since_time}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for txn in data:
            assert txn["timestamp"] >= since_time
    
    def test_list_transactions_invalid_limit(self):
        """Тест з некоректним значенням limit"""
        response = client.get("/transactions?limit=0")
        assert response.status_code == 422  # Validation error
    
    def test_list_transactions_limit_too_large(self):
        """Тест з занадто великим limit"""
        response = client.get("/transactions?limit=2000")
        assert response.status_code == 422  # Validation error


class TestStatsEndpoint:
    """Тести для GET /stats"""
    
    def test_stats_default(self):
        """Тест отримання статистики з дефолтними параметрами"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "since" in data
        assert "now" in data
        assert "total" in data
        assert "timeline" in data
        assert "GRANTED" in data["total"]
        assert "DENIED" in data["total"]
        assert isinstance(data["timeline"], list)
    
    def test_stats_with_hours_parameter(self):
        """Тест отримання статистики за певну кількість годин"""
        response = client.get("/stats?hours=12")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        # Перевіряємо що діапазон приблизно 12 годин
        time_range = data["now"] - data["since"]
        expected_range = 12 * 3600
        assert abs(time_range - expected_range) < 10  # допускаємо невелику похибку
    
    def test_stats_min_hours(self):
        """Тест статистики з мінімальним значенням hours"""
        response = client.get("/stats?hours=1")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
    
    def test_stats_invalid_hours_zero(self):
        """Тест статистики з некоректним значенням hours=0"""
        response = client.get("/stats?hours=0")
        assert response.status_code == 422  # Validation error
    
    def test_stats_invalid_hours_negative(self):
        """Тест статистики з негативним значенням hours"""
        response = client.get("/stats?hours=-5")
        assert response.status_code == 422  # Validation error
    
    def test_stats_structure(self):
        """Тест структури відповіді статистики"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Перевіряємо структуру total
        assert isinstance(data["total"]["GRANTED"], int)
        assert isinstance(data["total"]["DENIED"], int)
        
        # Перевіряємо структуру timeline
        for item in data["timeline"]:
            assert "t" in item
            assert "granted" in item
            assert "denied" in item
            assert isinstance(item["t"], (int, float))
            assert isinstance(item["granted"], int)
            assert isinstance(item["denied"], int)


class TestCORS:
    """Тести CORS налаштувань"""
    
    def test_cors_headers_present(self):
        """Тест наявності CORS headers"""
        response = client.options(
            "/transactions",
            headers={"Origin": "http://localhost:5173"}
        )
        # CORS middleware має додавати відповідні заголовки
        assert response.status_code in [200, 204]


class TestEdgeCases:
    """Тести граничних випадків"""
    
    def test_transaction_with_whitespace_uid(self):
        """Тест транзакції з пробілами в UID"""
        payload = {
            "uid": "  SPACEUID  ",
            "status": "GRANTED"
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200
    
    def test_transaction_with_very_old_timestamp(self):
        """Тест транзакції з дуже старим timestamp"""
        payload = {
            "uid": "OLDUID",
            "status": "GRANTED",
            "timestamp": 946684800.0  # 2000-01-01
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200
    
    def test_transaction_with_future_timestamp(self):
        """Тест транзакції з майбутнім timestamp"""
        payload = {
            "uid": "FUTUREUID",
            "status": "GRANTED",
            "timestamp": time.time() + 86400  # завтра
        }
        response = client.post("/transactions", json=payload)
        assert response.status_code == 200


# Запуск тестів: pytest test_server.py -v
# З покриттям коду: pytest test_server.py -v --cov=server --cov-report=html

