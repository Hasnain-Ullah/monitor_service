# tests/test_checker.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import checker


def test_check_endpoint_success():
    """Test that a successful request is recorded correctly"""
    config = {
        'url': 'https://httpbin.org/status/200',
        'method': 'GET',
        'timeout': 10,
        'expected_status': 200
    }
    
    result = checker.check_endpoint(config)
    
    assert result['success'] == True
    assert result['status_code'] == 200
    assert result['response_time'] > 0
    assert result['error_message'] is None
    print("✅ test_check_endpoint_success passed!")


def test_check_endpoint_failure():
    """Test that a failed request is recorded correctly"""
    config = {
        'url': 'https://httpbin.org/status/500',
        'method': 'GET',
        'timeout': 10,
        'expected_status': 200
    }
    
    result = checker.check_endpoint(config)
    
    assert result['success'] == False
    assert result['status_code'] == 500
    print("✅ test_check_endpoint_failure passed!")


def test_check_endpoint_timeout():
    """Test that a timeout is recorded correctly"""
    config = {
        'url': 'https://httpbin.org/delay/10',
        'method': 'GET',
        'timeout': 1,
        'expected_status': 200
    }
    
    result = checker.check_endpoint(config)
    
    assert result['success'] == False
    assert result['error_message'] == 'Timeout'
    print("✅ test_check_endpoint_timeout passed!")


def test_check_endpoint_connection_error():
    """Test that a connection error is recorded correctly"""
    config = {
        'url': 'http://127.0.0.1:9999/nonexistent',
        'method': 'GET',
        'timeout': 2,
        'expected_status': 200
    }
    
    result = checker.check_endpoint(config)
    
    assert result['success'] == False
    # Accept either Timeout or Connection Error since different systems may behave differently
    assert result['error_message'] in ['Timeout', 'Connection Error'] or 'Connection' in str(result['error_message'])
    print("✅ test_check_endpoint_connection_error passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 RUNNING CHECKER TESTS")
    print("=" * 50)
    test_check_endpoint_success()
    test_check_endpoint_failure()
    test_check_endpoint_timeout()
    test_check_endpoint_connection_error()
    print("\n🎉 All checker tests passed!")