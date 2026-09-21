# app/reporters.py

from datetime import datetime
from . import calculator


def print_status_summary(config, states, database):
    """
    Print a summary table of all monitored endpoints.
    
    Args:
        config: Full configuration
        states: State manager's state dict
        database: Database module
    """
    print("\n" + "=" * 100)
    print("📊 MONITORING STATUS SUMMARY")
    print("=" * 100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Table headers
    print(f"{'Endpoint':<30} | {'Status':<12} | {'Availability':<12} | {'Avg Latency':<12} | {'P95':<10} | {'Last Checked':<20}")
    print("-" * 100)
    
    for endpoint in config['endpoints']:
        url = endpoint['url']
        name = endpoint.get('name', url)
        
        # Get state
        state_info = states.get(url, {})
        current_state = state_info.get('state', 'UNKNOWN')
        
        # Get recent checks from database
        recent = database.get_recent_checks(url, limit=20)
        
        # Calculate stats
        if recent:
            formatted = [
                {'response_time': r['response_time'], 'success': bool(r['success'])}
                for r in recent
            ]
            stats = calculator.calculate_statistics(formatted)
        else:
            stats = {}
        
        availability = stats.get('availability', 0)
        avg_latency = stats.get('avg_latency', 0)
        p95 = stats.get('p95_latency', 0)
        last_checked = recent[0]['timestamp'][11:19] if recent else "Never"
        
        # Color based on state
        state_display = current_state
        
        # Format display
        endpoint_display = name[:28] + ".." if len(name) > 30 else name
        availability_str = f"{availability}%" if availability > 0 else "—"
        avg_str = f"{round(avg_latency*1000)}ms" if avg_latency > 0 else "—"
        p95_str = f"{round(p95*1000)}ms" if p95 > 0 else "—"
        
        print(f"{endpoint_display:<30} | {state_display:<12} | {availability_str:<12} | {avg_str:<12} | {p95_str:<10} | {last_checked:<20}")
    
    print("=" * 100)
    
    # Show active incidents
    active = database.get_active_incidents()
    if active:
        print("\n🚨 ACTIVE INCIDENTS")
        print("-" * 60)
        for inc in active:
            print(f"  [{inc['incident_type']}] {inc['endpoint']}")
            print(f"    Started: {inc['started_at'][11:19]}")
            print(f"    Reason: {inc['reason']}")
    else:
        print("\n✅ No active incidents")
    
    print("=" * 100 + "\n")