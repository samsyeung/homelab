#!/usr/bin/env python3

import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def update_grafana_time_params(url, minutes_ago=30):
    """
    Update Grafana URL time parameters to show data from X minutes ago to now.
    
    Args:
        url (str): The Grafana URL to update
        minutes_ago (int): How many minutes back to set the 'from' parameter
        
    Returns:
        str: Updated URL with new time parameters
    """
    if not url:
        return url
        
    now_ms = int(time.time() * 1000)
    from_ms = now_ms - (minutes_ago * 60 * 1000)
    
    # Parse the URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Update time parameters
    query_params['from'] = [str(from_ms)]
    query_params['to'] = [str(now_ms)]
    
    # Rebuild the URL
    new_query = urlencode(query_params, doseq=True)
    updated_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return updated_url

def process_dashboards(dashboards):
    """
    Process Grafana dashboard configurations and update time parameters.
    
    Args:
        dashboards (list): List of dashboard configurations
        
    Returns:
        list: Updated dashboard configurations with current time parameters
    """
    updated_dashboards = []
    for dashboard in dashboards:
        updated_dashboard = {
            'name': dashboard.get('name'),
            'url': update_grafana_time_params(dashboard.get('url', '')),
            'height': dashboard.get('height', 400)
        }
        updated_dashboards.append(updated_dashboard)
    
    return updated_dashboards