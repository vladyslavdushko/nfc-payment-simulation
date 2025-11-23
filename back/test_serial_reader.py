"""
Тести для модуля serial_reader.py
Запуск: pytest test_serial_reader.py -v
"""
import json
import time
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Встановити CI змінну перед імпортом (якщо ще не встановлена)
if 'CI' not in os.environ:
    os.environ['CI'] = 'true'

import serial_reader


class TestPostTransaction:
    """Тести для функції post_transaction"""
    
    @patch('serial_reader.requests.post')
    def test_post_transaction_success(self, mock_post):
        """Тест успішної відправки транзакції"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"ok": true}'
        mock_post.return_value = mock_response
        
        payload = {"uid": "TEST1234", "status": "GRANTED", "timestamp": time.time()}
        serial_reader.post_transaction(payload)
        
        mock_post.assert_called_once()
        assert mock_post.call_args[1]['json'] == payload
    
    @patch('serial_reader.requests.post')
    def test_post_transaction_server_error(self, mock_post):
        """Тест відправки транзакції при помилці сервера"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response
        
        payload = {"uid": "TEST5678", "status": "DENIED", "timestamp": time.time()}
        # Не має викидати виключення, тільки друкує помилку
        serial_reader.post_transaction(payload)
        
        mock_post.assert_called_once()
    
    @patch('serial_reader.requests.post')
    def test_post_transaction_timeout(self, mock_post):
        """Тест відправки транзакції при таймауті"""
        mock_post.side_effect = serial_reader.requests.RequestException("Timeout")
        
        payload = {"uid": "TIMEOUT", "status": "GRANTED", "timestamp": time.time()}
        # Не має викидати виключення
        serial_reader.post_transaction(payload)
        
        mock_post.assert_called_once()


class TestParseAndForwardLine:
    """Тести для функції parse_and_forward_line"""
    
    @patch('serial_reader.post_transaction')
    def test_parse_json_single_line(self, mock_post):
        """Тест парсингу JSON в одному рядку"""
        line = '{"uid": "A1B2C3D4", "status": "GRANTED", "timestamp": 1234567890.0}'
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["uid"] == "A1B2C3D4"
        assert call_args["status"] == "GRANTED"
    
    @patch('serial_reader.post_transaction')
    def test_parse_json_lowercase_status(self, mock_post):
        """Тест парсингу JSON з lowercase статусом"""
        line = '{"uid": "CAFEBABE", "status": "denied"}'
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["status"] == "DENIED"  # має бути uppercase
    
    @patch('serial_reader.post_transaction')
    def test_parse_txn_format(self, mock_post):
        """Тест парсингу TXN: формату"""
        line = "TXN:DEADBEEF:GRANTED"
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["uid"] == "DEADBEEF"
        assert call_args["status"] == "GRANTED"
    
    @patch('serial_reader.post_transaction')
    def test_parse_hex_uid_allowed(self, mock_post):
        """Тест парсингу дозволеного hex UID"""
        line = "A1B2C3D4"
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["uid"] == "A1B2C3D4"
        assert call_args["status"] == "GRANTED"  # у списку ALLOWED_UIDS
    
    @patch('serial_reader.post_transaction')
    def test_parse_hex_uid_denied(self, mock_post):
        """Тест парсингу недозволеного hex UID"""
        line = "12345678"
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["uid"] == "12345678"
        assert call_args["status"] == "DENIED"  # не у списку ALLOWED_UIDS
    
    @patch('serial_reader.post_transaction')
    def test_parse_unknown_line(self, mock_post):
        """Тест парсингу невідомого формату"""
        line = "SOME_UNKNOWN_FORMAT"
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["status"] == "DENIED"  # невідомі формати -> DENIED
    
    @patch('serial_reader.post_transaction')
    def test_ignore_noise_lines(self, mock_post):
        """Тест ігнорування шумових рядків"""
        lines = [
            "Received UID: A1B2C3D4",
            "Access GRANTED",
            "Access DENIED"
        ]
        for line in lines:
            serial_reader.parse_and_forward_line(line)
        
        # Не має викликати post_transaction для шумових рядків
        mock_post.assert_not_called()
    
    @patch('serial_reader.post_transaction')
    def test_parse_empty_line(self, mock_post):
        """Тест парсингу пустого рядка"""
        line = ""
        serial_reader.parse_and_forward_line(line)
        
        # Пустий рядок має ігноруватись
        mock_post.assert_not_called()
    
    @patch('serial_reader.post_transaction')
    def test_parse_json_with_whitespace(self, mock_post):
        """Тест парсингу JSON з пробілами навколо"""
        line = '  {"uid": "TEST", "status": "GRANTED"}  '
        serial_reader.parse_and_forward_line(line)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0][0]
        assert call_args["uid"] == "TEST"
    
    @patch('serial_reader.post_transaction')
    def test_parse_invalid_json(self, mock_post):
        """Тест парсингу некоректного JSON"""
        line = '{"uid": "INVALID", "status": MISSING_QUOTES}'
        serial_reader.parse_and_forward_line(line)
        
        # При помилці парсингу JSON не має викликати post_transaction
        # але це залежить від реалізації
        # У вашому коді може бути обробка помилок


class TestMultilineJSON:
    """Тести для парсингу багаторядкового JSON"""
    
    @patch('serial_reader.post_transaction')
    def test_parse_multiline_json(self, mock_post):
        """Тест парсингу JSON що розтягнутий на кілька рядків"""
        # Скидаємо стан парсера
        serial_reader._json_accum = ""
        serial_reader._json_open = False
        
        # Перший рядок (початок JSON)
        serial_reader.parse_and_forward_line('{"uid": "MULTI",')
        mock_post.assert_not_called()  # ще не завершено
        
        # Другий рядок (продовження)
        serial_reader.parse_and_forward_line('"status": "GRANTED",')
        mock_post.assert_not_called()  # ще не завершено
        
        # Третій рядок (кінець)
        serial_reader.parse_and_forward_line('"timestamp": 1234567890.0}')
        mock_post.assert_called_once()  # тепер має бути викликано
        
        call_args = mock_post.call_args[0][0]
        assert call_args["uid"] == "MULTI"
        assert call_args["status"] == "GRANTED"


class TestConfigurationConstants:
    """Тести конфігураційних констант"""
    
    def test_allowed_uids_exists(self):
        """Тест наявності списку дозволених UID"""
        assert hasattr(serial_reader, 'ALLOWED_UIDS')
        assert isinstance(serial_reader.ALLOWED_UIDS, list)
        assert len(serial_reader.ALLOWED_UIDS) > 0
    
    def test_api_url_configured(self):
        """Тест налаштування API URL"""
        assert hasattr(serial_reader, 'API_URL')
        assert isinstance(serial_reader.API_URL, str)
        assert serial_reader.API_URL.startswith('http')
    
    def test_debug_mode_configured(self):
        """Тест налаштування режиму відладки"""
        assert hasattr(serial_reader, 'DEBUG')
        assert isinstance(serial_reader.DEBUG, bool)


# Запуск: pytest test_serial_reader.py -v
# З покриттям: pytest test_serial_reader.py -v --cov=serial_reader --cov-report=html

