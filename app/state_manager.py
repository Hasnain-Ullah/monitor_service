# app/state_manager.py

from datetime import datetime
from . import calculator


class StateManager:
    """
    Manages the health state of monitored endpoints.
    
    States:
    - UP: API is operating normally
    - DEGRADED: API is responding but performance/reliability is below threshold
    - DOWN: API is unavailable or repeatedly failing
    - RECOVERED: API has returned to normal after being DOWN or DEGRADED
    """
    
    def __init__(self, config):
        """
        Initialize StateManager with configuration.
        
        Args:
            config: Full configuration dictionary
        """
        self.config = config
        self.monitoring = config.get('monitoring', {})
        
        # State thresholds
        self.consecutive_failures_for_down = self.monitoring.get('consecutive_failures_for_down', 3)
        self.availability_threshold = self.monitoring.get('availability_threshold', 95.0)
        self.latency_threshold_ms = self.monitoring.get('latency_threshold_ms', 500)
        self.recovery_successes = self.monitoring.get('recovery_successes', 2)
        self.window_size = self.monitoring.get('window_size', 20)
        self.min_checks_for_degraded = self.monitoring.get('min_checks_for_degraded', 5)
        
        # Per-endpoint state
        self.states = {}
        
        # Initialize states
        for endpoint in config['endpoints']:
            url = endpoint['url']
            self.states[url] = {
                'state': 'UP',
                'previous_state': None,
                'consecutive_failures': 0,
                'consecutive_successes': 0,
                'recent_checks': [],
                'last_state_change': None,
                'incident_start': None,
            }
    
    def get_state(self, url):
        """Get current state for an endpoint."""
        return self.states.get(url, {}).get('state', 'UNKNOWN')
    
    def update(self, url, check_result):
        """
        Update the state based on a new check result.
        
        Args:
            url: The endpoint URL
            check_result: Dict from checker.check_endpoint()
        
        Returns:
            Dict with old_state, new_state, changed, reason, stats
        """
        if url not in self.states:
            self.states[url] = {
                'state': 'UP',
                'previous_state': None,
                'consecutive_failures': 0,
                'consecutive_successes': 0,
                'recent_checks': [],
                'last_state_change': None,
                'incident_start': None,
            }
        
        state = self.states[url]
        old_state = state['state']
        
        # Update recent checks (keep only window_size)
        state['recent_checks'].append(check_result)
        if len(state['recent_checks']) > self.window_size:
            state['recent_checks'] = state['recent_checks'][-self.window_size:]
        
        # Update counters
        if check_result['success']:
            state['consecutive_failures'] = 0
            state['consecutive_successes'] += 1
        else:
            state['consecutive_failures'] += 1
            state['consecutive_successes'] = 0
        
        # Get endpoint-specific config
        endpoint_config = next(
            (e for e in self.config['endpoints'] if e['url'] == url),
            {}
        )
        latency_threshold = endpoint_config.get('latency_threshold_ms', self.latency_threshold_ms)
        
        # Calculate statistics from recent checks
        stats = calculator.calculate_statistics(state['recent_checks'])
        p95_latency = stats.get('p95_latency', 0)
        availability = stats.get('availability', 100)
        
        # Determine new state
        new_state = old_state
        reason = "No change"
        
        # ============================================
        # RULE 1: DOWN - 3 consecutive failures
        # ============================================
        if state['consecutive_failures'] >= self.consecutive_failures_for_down:
            if old_state != 'DOWN':
                new_state = 'DOWN'
                reason = f"{state['consecutive_failures']} consecutive failures"
                state['incident_start'] = datetime.now().isoformat()
        
        # ============================================
        # RULE 2: RECOVERED - Success after DOWN
        # ============================================
        elif old_state == 'DOWN' and check_result['success']:
            if state['consecutive_successes'] >= self.recovery_successes:
                new_state = 'UP'
                reason = f"Recovered after {state['consecutive_successes']} successful checks"
            else:
                new_state = 'RECOVERED'
                reason = f"Recovered after {state['consecutive_successes']} successful check(s)"
        
        # ============================================
        # RULE 3: DEGRADED - High latency or low availability
        # Only if we have enough checks
        # ============================================
        elif old_state in ['UP', 'RECOVERED']:
            # Only check for DEGRADED if we have enough data
            has_enough_data = len(state['recent_checks']) >= self.min_checks_for_degraded
            
            if has_enough_data:
                # Check high latency
                if p95_latency * 1000 > latency_threshold:
                    new_state = 'DEGRADED'
                    reason = f"P95 latency {round(p95_latency*1000)}ms > threshold {latency_threshold}ms"
                    if old_state != 'DEGRADED':
                        state['incident_start'] = datetime.now().isoformat()
                # Check low availability
                elif availability < self.availability_threshold:
                    new_state = 'DEGRADED'
                    reason = f"Availability {availability}% < threshold {self.availability_threshold}%"
                    if old_state != 'DEGRADED':
                        state['incident_start'] = datetime.now().isoformat()
                else:
                    new_state = 'UP'
                    reason = "Operating normally"
            else:
                # Not enough data yet, stay UP if currently UP
                if old_state == 'UP':
                    new_state = 'UP'
                    reason = f"Waiting for more data ({len(state['recent_checks'])}/{self.min_checks_for_degraded})"
        
        # ============================================
        # RULE 4: From DEGRADED to UP
        # ============================================
        elif old_state == 'DEGRADED' and check_result['success']:
            if p95_latency * 1000 <= latency_threshold and availability >= self.availability_threshold:
                new_state = 'UP'
                reason = "Latency and availability back to normal"
        
        # Update state
        if new_state != old_state:
            state['previous_state'] = old_state
            state['state'] = new_state
            state['last_state_change'] = datetime.now().isoformat()
            
            # Clear incident when recovered
            if new_state == 'UP' and old_state in ['DOWN', 'DEGRADED']:
                state['incident_start'] = None
        
        return {
            'old_state': old_state,
            'new_state': state['state'],
            'changed': new_state != old_state,
            'reason': reason,
            'stats': stats,
        }