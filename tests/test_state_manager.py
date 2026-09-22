# tests/test_state_manager.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.state_manager import StateManager


def test_initial_state_is_up():
    """Test that a new endpoint starts in UP state"""
    config = {
        'monitoring': {'consecutive_failures_for_down': 3, 'window_size': 20},
        'endpoints': [{'url': 'http://test.com', 'latency_threshold_ms': 500}]
    }
    sm = StateManager(config)
    assert sm.get_state('http://test.com') == 'UP'
    print("✅ test_initial_state_is_up passed!")


def test_up_to_down_after_3_failures():
    """Test UP → 3 failures → DOWN"""
    config = {
        'monitoring': {'consecutive_failures_for_down': 3, 'window_size': 20},
        'endpoints': [{'url': 'http://test.com', 'latency_threshold_ms': 500}]
    }
    sm = StateManager(config)
    
    # Initial state
    assert sm.get_state('http://test.com') == 'UP'
    
    # 1 failure - still UP
    sm.update('http://test.com', {'success': False, 'response_time': 0.1, 'status_code': 500})
    assert sm.get_state('http://test.com') == 'UP', "1 failure should not change state"
    
    # 2 failures - still UP
    sm.update('http://test.com', {'success': False, 'response_time': 0.1, 'status_code': 500})
    assert sm.get_state('http://test.com') == 'UP', "2 failures should not change state"
    
    # 3 failures - DOWN
    sm.update('http://test.com', {'success': False, 'response_time': 0.1, 'status_code': 500})
    assert sm.get_state('http://test.com') == 'DOWN', "3 failures should change to DOWN"
    
    print("✅ test_up_to_down_after_3_failures passed!")


def test_down_to_recovered_to_up():
    """Test DOWN → success → RECOVERED → UP"""
    config = {
        'monitoring': {'consecutive_failures_for_down': 3, 'recovery_successes': 2, 'window_size': 20},
        'endpoints': [{'url': 'http://test.com', 'latency_threshold_ms': 500}]
    }
    sm = StateManager(config)
    
    # Go DOWN
    for _ in range(3):
        sm.update('http://test.com', {'success': False, 'response_time': 0.1, 'status_code': 500})
    assert sm.get_state('http://test.com') == 'DOWN'
    
    # 1 success - RECOVERED
    sm.update('http://test.com', {'success': True, 'response_time': 0.05, 'status_code': 200})
    assert sm.get_state('http://test.com') == 'RECOVERED', "1 success after DOWN should be RECOVERED"
    
    # 2nd success - UP
    sm.update('http://test.com', {'success': True, 'response_time': 0.05, 'status_code': 200})
    assert sm.get_state('http://test.com') == 'UP', "2 successes should change to UP"
    
    print("✅ test_down_to_recovered_to_up passed!")


def test_up_to_degraded_high_latency():
    """Test UP → high latency → DEGRADED"""
    config = {
        'monitoring': {'latency_threshold_ms': 500, 'window_size': 20},
        'endpoints': [{'url': 'http://test.com', 'latency_threshold_ms': 500}]
    }
    sm = StateManager(config)
    
    # Add slow checks (P95 will exceed threshold)
    for _ in range(10):
        sm.update('http://test.com', {'success': True, 'response_time': 1.5, 'status_code': 200})
    
    assert sm.get_state('http://test.com') == 'DEGRADED', "High latency should change to DEGRADED"
    print("✅ test_up_to_degraded_high_latency passed!")


def test_degraded_to_up():
    """Test DEGRADED → normal latency → UP"""
    config = {
        'monitoring': {'latency_threshold_ms': 500, 'window_size': 20},
        'endpoints': [{'url': 'http://test.com', 'latency_threshold_ms': 500}]
    }
    sm = StateManager(config)
    
    # Go DEGRADED
    for _ in range(10):
        sm.update('http://test.com', {'success': True, 'response_time': 1.5, 'status_code': 200})
    assert sm.get_state('http://test.com') == 'DEGRADED'
    
    # Add fast checks to recover
    for _ in range(20):
        sm.update('http://test.com', {'success': True, 'response_time': 0.05, 'status_code': 200})
    assert sm.get_state('http://test.com') == 'UP', "Normal latency should change to UP"
    
    print("✅ test_degraded_to_up passed!")


def test_one_failure_stays_up():
    """Test UP → 1 failure → UP (not DOWN or DEGRADED)"""
    config = {
        'monitoring': {'consecutive_failures_for_down': 3, 'window_size': 20},
        'endpoints': [{'url': 'http://test.com', 'latency_threshold_ms': 500}]
    }
    sm = StateManager(config)
    
    sm.update('http://test.com', {'success': False, 'response_time': 0.1, 'status_code': 500})
    assert sm.get_state('http://test.com') == 'UP', "1 failure should stay UP"
    
    print("✅ test_one_failure_stays_up passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 RUNNING STATE MANAGER TESTS")
    print("=" * 50)
    test_initial_state_is_up()
    test_up_to_down_after_3_failures()
    test_down_to_recovered_to_up()
    test_up_to_degraded_high_latency()
    test_degraded_to_up()
    test_one_failure_stays_up()
    print("\n🎉 All tests passed!")