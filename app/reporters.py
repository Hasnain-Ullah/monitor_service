# app/reporters.py

import json
import csv
import os
from datetime import datetime
from . import calculator


def print_status_summary(config, states, database):
    """
    Print a summary table of all monitored endpoints.
    Also saves the summary to reports/ folder.
    """
    print("\n" + "=" * 100)
    print("📊 MONITORING STATUS SUMMARY")
    print("=" * 100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Build summary data
    summary_rows = []
    
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
        
        # Format display
        endpoint_display = name[:28] + ".." if len(name) > 30 else name
        availability_str = f"{availability}%" if availability > 0 else "—"
        avg_str = f"{round(avg_latency*1000)}ms" if avg_latency > 0 else "—"
        p95_str = f"{round(p95*1000)}ms" if p95 > 0 else "—"
        
        print(f"{endpoint_display:<30} | {current_state:<12} | {availability_str:<12} | {avg_str:<12} | {p95_str:<10} | {last_checked:<20}")
        
        # Add to summary rows for file saving
        summary_rows.append({
            'endpoint': name,
            'url': url,
            'status': current_state,
            'availability': availability,
            'avg_latency_ms': round(avg_latency * 1000, 2),
            'p95_latency_ms': round(p95 * 1000, 2),
            'last_checked': last_checked,
        })
    
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
    
    # Save reports to files
    _save_reports(summary_rows, active)


def _save_reports(summary_rows, active_incidents):
    """Save summary and incidents to report files."""
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ============================================
    # SAVE JSON REPORT
    # ============================================
    json_report = {
        'timestamp': datetime.now().isoformat(),
        'summary': summary_rows,
        'active_incidents': active_incidents,
        'total_endpoints': len(summary_rows),
        'endpoints_up': len([r for r in summary_rows if r['status'] == 'UP']),
        'endpoints_degraded': len([r for r in summary_rows if r['status'] == 'DEGRADED']),
        'endpoints_down': len([r for r in summary_rows if r['status'] == 'DOWN']),
    }
    
    json_path = f"reports/status_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(json_report, f, indent=2)
    print(f"✅ JSON report saved: {json_path}")
    
    # Also save latest as status_latest.json
    latest_json_path = "reports/status_latest.json"
    with open(latest_json_path, 'w') as f:
        json.dump(json_report, f, indent=2)
    
    # ============================================
    # SAVE CSV REPORT
    # ============================================
    csv_path = f"reports/status_{timestamp}.csv"
    with open(csv_path, 'w', newline='') as f:
        fieldnames = ['endpoint', 'url', 'status', 'availability', 'avg_latency_ms', 'p95_latency_ms', 'last_checked']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"✅ CSV report saved: {csv_path}")
    
    # Also save latest as status_latest.csv
    latest_csv_path = "reports/status_latest.csv"
    with open(latest_csv_path, 'w', newline='') as f:
        fieldnames = ['endpoint', 'url', 'status', 'availability', 'avg_latency_ms', 'p95_latency_ms', 'last_checked']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def save_incident_report(database, filename="reports/incidents.json"):
    """Save all incidents to a JSON file."""
    os.makedirs("reports", exist_ok=True)
    
    # Get all incidents (active and resolved)
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY id DESC")
    incidents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_incidents': len(incidents),
        'active_incidents': len([i for i in incidents if i['status'] == 'active']),
        'resolved_incidents': len([i for i in incidents if i['status'] == 'resolved']),
        'incidents': incidents,
    }
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Incident report saved: {filename}")