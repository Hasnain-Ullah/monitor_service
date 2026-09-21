# app/calculator.py

import statistics


def calculate_percentile(data, p):
    """
    Calculate p-th percentile using linear interpolation.
    
    Args:
        data: Sorted list of numbers
        p: Percentile (0-100)
    
    Returns:
        Float: The p-th percentile value
    """
    if not data:
        return 0
    
    n = len(data)
    
    if n == 1:
        return data[0]
    
    rank = (n - 1) * (p / 100)
    lower_idx = int(rank)
    upper_idx = lower_idx + 1
    
    if rank == lower_idx:
        return data[lower_idx]
    
    lower_value = data[lower_idx]
    upper_value = data[upper_idx] if upper_idx < n else data[lower_idx]
    fraction = rank - lower_idx
    
    return lower_value + (upper_value - lower_value) * fraction


def calculate_statistics(results):
    """
    Calculate statistics from a list of results.
    
    Args:
        results: List of dicts with 'response_time' and 'success'
    
    Returns:
        Dict with statistics
    """
    if not results:
        return {}
    
    response_times = [r['response_time'] for r in results]
    successful = [r for r in results if r['success']]
    
    total = len(results)
    success_count = len(successful)
    availability = (success_count / total) * 100 if total > 0 else 0
    
    sorted_times = sorted(response_times)
    
    return {
        'total_checks': total,
        'successful': success_count,
        'failed': total - success_count,
        'availability': round(availability, 2),
        'avg_latency': round(statistics.mean(response_times), 4) if response_times else 0,
        'min_latency': round(min(response_times), 4) if response_times else 0,
        'max_latency': round(max(response_times), 4) if response_times else 0,
        'p50_latency': round(calculate_percentile(sorted_times, 50), 4) if sorted_times else 0,
        'p95_latency': round(calculate_percentile(sorted_times, 95), 4) if sorted_times else 0,
        'p99_latency': round(calculate_percentile(sorted_times, 99), 4) if sorted_times else 0,
    }