import json
import os
from typing import Dict, Any

import requests

from app.core.settings import settings


def send_sla_alert(payload: Dict[str, Any], dry_run: bool = True) -> bool:
    """
    Send SLA breach alert to Microsoft Teams.
    
    Args:
        payload: Alert payload dictionary
        dry_run: If True, only print the payload without sending
        
    Returns:
        True if successful, False otherwise
    """
    # Prepare the Teams message format
    teams_message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "FF0000" if payload.get("breaches", 0) > 0 else "00FF00",
        "summary": payload.get("title", "SLA Alert"),
        "sections": [
            {
                "activityTitle": payload.get("title", "SLA Breach Alert"),
                "activitySubtitle": f"Window: {payload.get('window', 'Unknown')}",
                "facts": [
                    {
                        "name": "SLA Breaches",
                        "value": str(payload.get("breaches", 0))
                    },
                    {
                        "name": "Top Assays",
                        "value": ", ".join([f"{a['assay']}({a['breaches']})" for a in payload.get("top_assays", [])])
                    }
                ]
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "View Dashboard",
                "targets": [
                    {
                        "os": "default",
                        "uri": payload.get("link", "http://localhost:8501")
                    }
                ]
            }
        ]
    }
    
    # Print payload for dry-run or debugging
    print("Teams Alert Payload:")
    print(json.dumps(teams_message, indent=2, default=str))
    
    if dry_run or not settings.TEAMS_WEBHOOK_URL:
        print("DRY RUN: Alert not sent (dry_run=True or no webhook URL configured)")
        return True
    
    try:
        # Send to Teams webhook
        response = requests.post(
            settings.TEAMS_WEBHOOK_URL,
            json=teams_message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Alert sent successfully to Teams")
            return True
        else:
            print(f"Failed to send alert: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error sending Teams alert: {e}")
        return False


def create_sla_alert_payload(breach_count: int, top_assays: list, window: str = "last 24h") -> Dict[str, Any]:
    """
    Create a standardized SLA alert payload.
    
    Args:
        breach_count: Number of SLA breaches
        top_assays: List of dicts with assay and breach count
        window: Time window description
        
    Returns:
        Formatted payload dictionary
    """
    return {
        "title": "SLA Breach Alert" if breach_count > 0 else "SLA Status OK",
        "breaches": breach_count,
        "top_assays": top_assays,
        "window": window,
        "link": "http://localhost:8501"
    }


def send_standup_summary(summary_data: Dict[str, Any], dry_run: bool = True) -> bool:
    """
    Send stand-up summary to Teams.
    
    Args:
        summary_data: Stand-up summary data
        dry_run: If True, only print the payload without sending
        
    Returns:
        True if successful, False otherwise
    """
    teams_message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": "Daily Stand-up Summary",
        "sections": [
            {
                "activityTitle": "LabOps Daily Stand-up",
                "activitySubtitle": summary_data.get("date", "Today"),
                "facts": [
                    {
                        "name": "Total Specimens",
                        "value": str(summary_data.get("total_specimens", 0))
                    },
                    {
                        "name": "TAT P90 (min)",
                        "value": f"{summary_data.get('tat_p90', 0):.1f}"
                    },
                    {
                        "name": "Error Rate",
                        "value": f"{summary_data.get('error_rate', 0):.1%}"
                    },
                    {
                        "name": "SLA Breaches",
                        "value": str(summary_data.get("sla_breaches", 0))
                    }
                ]
            }
        ]
    }
    
    # Print payload for dry-run or debugging
    print("Stand-up Summary Payload:")
    print(json.dumps(teams_message, indent=2, default=str))
    
    if dry_run or not settings.TEAMS_WEBHOOK_URL:
        print("DRY RUN: Stand-up summary not sent")
        return True
    
    try:
        response = requests.post(
            settings.TEAMS_WEBHOOK_URL,
            json=teams_message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Stand-up summary sent successfully to Teams")
            return True
        else:
            print(f"Failed to send stand-up summary: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error sending stand-up summary: {e}")
        return False
