"""
Навантажувальне тестування API за допомогою Locust
Запуск: locust -f locustfile.py --host=https://127.0.0.1:8443
Web UI: http://localhost:8089

Headless режим:
locust -f locustfile.py --host=https://127.0.0.1:8443 --users 50 --spawn-rate 5 --run-time 2m --headless --html load-report.html
"""
import time
import random
from locust import HttpUser, task, between


class NFCPaymentAPIUser(HttpUser):
    """Симулює користувача який взаємодіє з NFC Payment API"""
    
    # Час очікування між запитами (1-3 секунди)
    wait_time = between(1, 3)
    
    # Вимкнути SSL перевірку для локального тестування
    insecure = True
    
    def on_start(self):
        """Викликається при старті кожного користувача"""
        self.client.verify = False  # Вимкнути SSL verification
        print(f"User {self.environment.runner.user_count} started")
    
    @task(10)
    def health_check(self):
        """Перевірка здоров'я сервісу (найчастіше)"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(8)
    def list_transactions(self):
        """Отримання списку транзакцій"""
        limits = [10, 20, 50, 100]
        limit = random.choice(limits)
        
        with self.client.get(
            f"/transactions?limit={limit}",
            catch_response=True,
            name="GET /transactions"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    response.success()
                else:
                    response.failure("Response is not a list")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(6)
    def list_transactions_filtered(self):
        """Отримання відфільтрованих транзакцій"""
        statuses = ["GRANTED", "DENIED"]
        status = random.choice(statuses)
        
        with self.client.get(
            f"/transactions?status={status}&limit=50",
            catch_response=True,
            name="GET /transactions (filtered)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Перевірити що всі транзакції мають правильний статус
                if isinstance(data, list):
                    if all(t.get('status') == status for t in data):
                        response.success()
                    else:
                        response.failure("Filter not working correctly")
                else:
                    response.failure("Response is not a list")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(5)
    def get_stats(self):
        """Отримання статистики"""
        hours_options = [1, 6, 12, 24]
        hours = random.choice(hours_options)
        
        with self.client.get(
            f"/stats?hours={hours}",
            catch_response=True,
            name="GET /stats"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                required_fields = ['since', 'now', 'total', 'timeline']
                if all(field in data for field in required_fields):
                    response.success()
                else:
                    response.failure("Missing required fields in response")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(15)
    def create_transaction_granted(self):
        """Створення транзакції зі статусом GRANTED"""
        uid = f"UID{random.randint(10000000, 99999999):08X}"
        payload = {
            "uid": uid,
            "status": "GRANTED",
            "timestamp": time.time()
        }
        
        with self.client.post(
            "/transactions",
            json=payload,
            catch_response=True,
            name="POST /transactions (GRANTED)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('id'):
                    response.success()
                else:
                    response.failure("Response doesn't have 'ok' or 'id'")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(5)
    def create_transaction_denied(self):
        """Створення транзакції зі статусом DENIED"""
        uid = f"DENY{random.randint(1000, 9999):04X}"
        payload = {
            "uid": uid,
            "status": "DENIED",
            "timestamp": time.time()
        }
        
        with self.client.post(
            "/transactions",
            json=payload,
            catch_response=True,
            name="POST /transactions (DENIED)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    response.success()
                else:
                    response.failure("Response doesn't have 'ok' field")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def create_transaction_without_timestamp(self):
        """Створення транзакції без timestamp (має використати серверний час)"""
        uid = f"NOTIME{random.randint(1000, 9999)}"
        payload = {
            "uid": uid,
            "status": random.choice(["GRANTED", "DENIED"])
        }
        
        with self.client.post(
            "/transactions",
            json=payload,
            catch_response=True,
            name="POST /transactions (no timestamp)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def test_invalid_request(self):
        """Тест невалідного запиту (має повернути 422)"""
        payload = {
            "uid": "",  # Пустий UID - невалідно
            "status": "GRANTED"
        }
        
        with self.client.post(
            "/transactions",
            json=payload,
            catch_response=True,
            name="POST /transactions (invalid)"
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(
                    f"Expected 422 for invalid request, got {response.status_code}"
                )


class AdminUser(HttpUser):
    """Симулює адміністратора який більше читає дані"""
    
    wait_time = between(2, 5)
    weight = 1  # Менше адмінів ніж звичайних користувачів
    
    def on_start(self):
        self.client.verify = False
    
    @task(20)
    def list_all_transactions(self):
        """Адмін переглядає всі транзакції"""
        self.client.get("/transactions?limit=1000")
    
    @task(15)
    def get_detailed_stats(self):
        """Адмін отримує детальну статистику"""
        for hours in [1, 6, 12, 24]:
            self.client.get(f"/stats?hours={hours}")
            time.sleep(0.5)
    
    @task(5)
    def search_by_uid(self):
        """Пошук транзакцій за UID"""
        # Генеруємо випадковий UID що може існувати
        uid = f"UID{random.randint(10000000, 99999999):08X}"
        self.client.get(f"/transactions?uid={uid}")


# Конфігурація для різних профілів навантаження

class LightLoadUser(HttpUser):
    """Легке навантаження - рідкісні запити"""
    wait_time = between(5, 10)
    weight = 3
    
    def on_start(self):
        self.client.verify = False
    
    @task
    def check_status(self):
        self.client.get("/health")
        self.client.get("/transactions?limit=10")


class HeavyLoadUser(HttpUser):
    """Важке навантаження - часті запити"""
    wait_time = between(0.5, 1.5)
    weight = 1
    
    def on_start(self):
        self.client.verify = False
    
    @task(5)
    def rapid_transactions(self):
        for _ in range(5):
            payload = {
                "uid": f"HEAVY{random.randint(1000, 9999)}",
                "status": random.choice(["GRANTED", "DENIED"])
            }
            self.client.post("/transactions", json=payload)
            time.sleep(0.1)
    
    @task(3)
    def rapid_reads(self):
        for _ in range(10):
            self.client.get("/transactions?limit=20")
            time.sleep(0.05)


# Запуск:
# 
# 1. Web UI режим (інтерактивно):
#    locust -f locustfile.py --host=https://127.0.0.1:8443
#    Потім відкрити http://localhost:8089
#
# 2. Headless режим (автоматично):
#    locust -f locustfile.py --host=https://127.0.0.1:8443 \
#           --users 50 --spawn-rate 5 --run-time 2m \
#           --headless --html load-report.html
#
# 3. Тільки NFCPaymentAPIUser:
#    locust -f locustfile.py --host=https://127.0.0.1:8443 \
#           NFCPaymentAPIUser
#
# 4. З CSV звітами:
#    locust -f locustfile.py --host=https://127.0.0.1:8443 \
#           --users 100 --spawn-rate 10 --run-time 5m \
#           --headless --csv=results --html=results.html

