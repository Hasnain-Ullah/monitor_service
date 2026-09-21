# app/checker.py

import requests
import time
from datetime import datetime


def check_endpoint(endpoint_config):
    """
    Send one HTTP request to an endpoint and record the result.
    
    Args:
        endpoint_config: Dict with url, method, timeout, etc.
    
    Returns:
        Dict with check result
    """
    url = endpoint_config['url']
    method = endpoint_config.get('method', 'GET').upper()
    timeout = endpoint_config.get('timeout', 5)
    expected_status = endpoint_config.get('expected_status', 200)
    headers = endpoint_config.get('headers', {})
    body = endpoint_config.get('body', None)
    
    start_time = time.time()
    success = False
    status_code = None
    error_message = None
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=body, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=body, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            response = requests.request(method, url, headers=headers, json=body, timeout=timeout)
        
        status_code = response.status_code
        success = (status_code == expected_status)
        
    except requests.exceptions.Timeout:
        error_message = "Timeout"
        success = False
    except requests.exceptions.ConnectionError:
        error_message = "Connection Error"
        success = False
    except Exception as e:
        error_message = str(e)
        success = False
    
    response_time = time.time() - start_time
    
    return {
        'url': url,
        'method': method,
        'timestamp': datetime.now().isoformat(),
        'response_time': round(response_time, 4),
        'status_code': status_code,
        'success': success,
        'error_message': error_message,
    }