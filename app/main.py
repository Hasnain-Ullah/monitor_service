# app/main.py

import sys
import os
import time
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config_loader, checker, state_manager, database, alerts, reporters


def main():
    """Main entry point for the monitoring service."""
    
    parser = argparse.ArgumentParser(description='API Monitoring Service')
    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Path to configuration file (JSON or YAML)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run one check cycle and exit (no continuous monitoring)'
    )
    parser.add_argument(
        '--webhook',
        help='Webhook URL for alerts (e.g., Slack webhook)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status and exit'
    )
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 API MONITORING SERVICE")
    print("=" * 80)
    
    # Load configuration
    print(f"\n📂 Loading config: {args.config}")
    config = config_loader.load_config(args.config)
    
    # Initialize database
    database.create_tables()
    print("✅ Database initialized")
    
    # Initialize state manager
    sm = state_manager.StateManager(config)
    print("✅ State manager initialized")
    
    # Initialize alert manager
    alert_mgr = alerts.AlertManager(webhook_url=args.webhook)
    if args.webhook:
        print(f"✅ Webhook configured: {args.webhook}")
    else:
        print("ℹ️ No webhook configured - alerts will print to console only")
    
    # Show status only
    if args.status:
        reporters.print_status_summary(config, sm.states, database)
        return
    
    # Get monitoring interval
    default_interval = config.get('monitoring', {}).get('default_interval', 30)
    
    print(f"\n📋 Monitoring {len(config['endpoints'])} endpoints")
    print(f"⏱️ Default interval: {default_interval}s")
    print("=" * 80)
    
    # Main monitoring loop
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n🔄 Check cycle #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 60)
            
            for endpoint in config['endpoints']:
                url = endpoint['url']
                name = endpoint.get('name', url)
                
                # Check endpoint
                result = checker.check_endpoint(endpoint)
                
                # Update state
                state_update = sm.update(url, result)
                new_state = state_update['new_state']
                old_state = state_update['old_state']
                changed = state_update['changed']
                reason = state_update['reason']
                
                # Save check to database
                database.save_check(
                    endpoint=url,
                    timestamp=result['timestamp'],
                    status_code=result['status_code'],
                    response_time=result['response_time'],
                    success=result['success'],
                    state=new_state,
                    error_message=result['error_message']
                )
                
                # Handle incident creation/resolution
                if changed:
                    extra = {}
                    
                    if new_state == 'DOWN':
                        # Create incident
                        database.create_incident(url, 'DOWN', reason)
                        if result['status_code']:
                            extra['last_status'] = result['status_code']
                        alert_mgr.process_state_change(url, old_state, new_state, reason, extra)
                    
                    elif new_state == 'DEGRADED':
                        # Create incident
                        database.create_incident(url, 'DEGRADED', reason)
                        latency = round(state_update['stats'].get('p95_latency', 0) * 1000)
                        extra['latency'] = latency
                        alert_mgr.process_state_change(url, old_state, new_state, reason, extra)
                    
                    elif new_state == 'UP' and old_state in ['DOWN', 'DEGRADED']:
                        # Resolve incident
                        resolved = database.resolve_incident(url, old_state)
                        if resolved:
                            duration = resolved['duration']
                            mins = int(duration // 60)
                            secs = int(duration % 60)
                            extra['downtime'] = f"{mins}m {secs}s"
                        latency = round(result['response_time'] * 1000)
                        extra['latency'] = latency
                        alert_mgr.process_state_change(url, old_state, new_state, reason, extra)
                
                # Print check result
                status_icon = "✅" if result['success'] else "❌"
                state_icon = {
                    'UP': '🟢',
                    'DEGRADED': '🟡',
                    'DOWN': '🔴',
                    'RECOVERED': '🔵',
                }.get(new_state, '⚪')
                
                print(f"  {status_icon} {name:<30} | {state_icon} {new_state:<12} | {round(result['response_time']*1000)}ms")
            
            reporters.print_status_summary(config, sm.states, database)

            # Save incident report
            reporters.save_incident_report(database)
            
            # Exit if --once
            if args.once:
                print("✅ Single check cycle complete.")
                break
            
            # Wait for next cycle
            print(f"⏱️ Waiting {default_interval}s before next check...")
            time.sleep(default_interval)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user.")
        reporters.print_status_summary(config, sm.states, database)


if __name__ == "__main__":
    main()