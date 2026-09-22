# tests/test_database.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import database


def test_create_tables():
    """Test that tables are created correctly"""
    database.create_tables()
    # If no error, tables exist
    print("✅ test_create_tables passed!")


def test_save_and_get_check():
    """Test saving a check and retrieving it"""
    # Save a check
    database.save_check(
        endpoint='http://test.com',
        timestamp='2026-09-21T14:30:00',
        status_code=200,
        response_time=0.045,
        success=True,
        state='UP'
    )
    
    # Retrieve it
    checks = database.get_recent_checks('http://test.com', limit=1)
    
    assert len(checks) == 1
    assert checks[0]['endpoint'] == 'http://test.com'
    assert checks[0]['status_code'] == 200
    assert checks[0]['success'] == 1
    print("✅ test_save_and_get_check passed!")


def test_create_and_resolve_incident():
    """Test creating and resolving an incident"""
    # Create incident
    incident_id = database.create_incident(
        endpoint='http://test.com',
        incident_type='DOWN',
        reason='3 consecutive failures'
    )
    
    assert incident_id > 0
    
    # Check active incidents
    active = database.get_active_incidents()
    assert len(active) > 0
    
    # Resolve incident
    resolved = database.resolve_incident('http://test.com', 'DOWN')
    
    assert resolved is not None
    assert resolved['duration'] > 0
    print("✅ test_create_and_resolve_incident passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 RUNNING DATABASE TESTS")
    print("=" * 50)
    test_create_tables()
    test_save_and_get_check()
    test_create_and_resolve_incident()
    print("\n🎉 All database tests passed!")