# app/alerts.py

import requests
from datetime import datetime


class AlertManager:
    """
    Sends webhook alerts when states change.
    
    Deduplication: Only sends an alert when the state changes.
    If the API remains DOWN for 20 checks, only 1 alert is sent.
    """
    
    def __init__(self, webhook_url=None):
        """
        Args:
            webhook_url: URL to send alerts (Slack webhook or test endpoint)
        """
        self.webhook_url = webhook_url
        self.last_states = {}  # Tracks last known state per endpoint
    
    def send_alert(self, endpoint, state, reason, extra=None):
        """
        Send an alert to the webhook.
        
        Args:
            endpoint: The API endpoint
            state: The new state (DOWN, DEGRADED, RECOVERED)
            reason: Why the state changed
            extra: Extra info (e.g., downtime, latency)
        """
        # Build message
        if state == 'DOWN':
            message = self._build_down_message(endpoint, reason, extra)
        elif state == 'DEGRADED':
            message = self._build_degraded_message(endpoint, reason, extra)
        elif state == 'RECOVERED':
            message = self._build_recovered_message(endpoint, reason, extra)
        else:
            return
        
        # Print to console
        print("\n" + "=" * 60)
        print(f"🚨 ALERT: {state}")
        print("=" * 60)
        print(message)
        print("=" * 60 + "\n")
        
        # Send to webhook if configured
        if self.webhook_url:
            try:
                response = requests.post(
                    self.webhook_url,
                    json={"text": message},
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"✅ Alert sent to webhook")
                else:
                    print(f"⚠️ Webhook returned {response.status_code}")
            except Exception as e:
                print(f"❌ Failed to send webhook: {e}")
    
    def process_state_change(self, endpoint, old_state, new_state, reason, extra=None):
        """
        Process a state change and send alerts only on meaningful changes.
        
        Deduplication logic:
        - Only send if state actually changed
        - Track last state per endpoint
        """
        if old_state == new_state:
            return False  # No change, no alert
        
        # Update last state
        self.last_states[endpoint] = new_state
        
        # Send alerts for specific transitions
        if new_state == 'DOWN':
            self.send_alert(endpoint, 'DOWN', reason, extra)
            return True
        elif new_state == 'DEGRADED':
            self.send_alert(endpoint, 'DEGRADED', reason, extra)
            return True
        elif new_state == 'RECOVERED' or (old_state in ['DOWN', 'DEGRADED'] and new_state == 'UP'):
            self.send_alert(endpoint, 'RECOVERED', reason, extra)
            return True
        
        return False
    
    def _build_down_message(self, endpoint, reason, extra):
        """Build DOWN alert message."""
        lines = [
            "🚨 API DOWN",
            f"Endpoint: {endpoint}",
            f"Reason: {reason}",
        ]
        if extra and 'last_status' in extra:
            lines.append(f"Last response: HTTP {extra['last_status']}")
        lines.append(f"Since: {datetime.now().strftime('%H:%M')}")
        return "\n".join(lines)
    
    def _build_degraded_message(self, endpoint, reason, extra):
        """Build DEGRADED alert message."""
        lines = [
            "⚠️ API DEGRADED",
            f"Endpoint: {endpoint}",
            f"Reason: {reason}",
        ]
        if extra and 'latency' in extra:
            lines.append(f"Latency: {extra['latency']}ms")
        lines.append(f"Since: {datetime.now().strftime('%H:%M')}")
        return "\n".join(lines)
    
    def _build_recovered_message(self, endpoint, reason, extra):
        """Build RECOVERED alert message."""
        lines = [
            "✅ API RECOVERED",
            f"Endpoint: {endpoint}",
            f"Reason: {reason}",
        ]
        if extra and 'downtime' in extra:
            lines.append(f"Downtime: {extra['downtime']}")
        if extra and 'latency' in extra:
            lines.append(f"Current latency: {extra['latency']}ms")
        return "\n".join(lines)