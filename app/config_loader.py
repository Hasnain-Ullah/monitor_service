# app/config_loader.py

import json
import yaml
import os


def load_config(file_path):
    """
    Load configuration from JSON or YAML file.
    
    Args:
        file_path: Path to config file (.json or .yaml)
    
    Returns:
        Dictionary with configuration settings
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    if file_path.endswith('.json'):
        config = json.loads(content)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        config = yaml.safe_load(content)
    else:
        raise ValueError("Config file must be .json or .yaml")
    
    # Validate config
    if 'endpoints' not in config:
        raise ValueError("Config must contain 'endpoints' key")
    
    if 'monitoring' not in config:
        config['monitoring'] = {}
    
    # Set defaults for monitoring
    monitoring = config['monitoring']
    monitoring.setdefault('consecutive_failures_for_down', 3)
    monitoring.setdefault('availability_threshold', 95.0)
    monitoring.setdefault('latency_threshold_ms', 500)
    monitoring.setdefault('recovery_successes', 2)
    monitoring.setdefault('window_size', 20)
    
    # Set defaults for each endpoint
    for endpoint in config['endpoints']:
        endpoint.setdefault('method', 'GET')
        endpoint.setdefault('interval', 30)
        endpoint.setdefault('timeout', 5)
        endpoint.setdefault('expected_status', 200)
        endpoint.setdefault('latency_threshold_ms', monitoring['latency_threshold_ms'])
        endpoint.setdefault('headers', {})
        endpoint.setdefault('body', None)
    
    return config