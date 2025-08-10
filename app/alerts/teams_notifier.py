"""
Microsoft Teams Alerting Module for LabOps Metrics
Handles SLA breach notifications and metric alerts
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from pydantic import BaseModel


class AlertPayload(BaseModel):
    """Structure for Teams alert payloads."""
    title: str
    summary: str
    text: str
    theme_color: str = "#FF0000"  # Red for alerts
    sections: Optional[list] = None
    potential_action: Optional[list] = None


class TeamsNotifier:
    """Handles Microsoft Teams webhook notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None, dry_run: bool = True):
        """
        Initialize Teams notifier.
        
        Args:
            webhook_url: Teams webhook URL (from TEAMS_WEBHOOK_URL env var)
            dry_run: If True, only log alerts without sending
        """
        self.webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
        self.dry_run = dry_run
        
        if not self.webhook_url and not dry_run:
            print("⚠️  Warning: No Teams webhook URL configured. Set TEAMS_WEBHOOK_URL environment variable.")
    
    def send_alert(self, payload: AlertPayload) -> bool:
        """
        Send alert to Teams channel.
        
        Args:
            payload: Alert payload to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if self.dry_run:
            print("🔔 [DRY RUN] Teams Alert:")
            print(f"   Title: {payload.title}")
            print(f"   Summary: {payload.summary}")
            print(f"   Text: {payload.text}")
            print(f"   Theme Color: {payload.theme_color}")
            if payload.sections:
                print(f"   Sections: {len(payload.sections)}")
            return True
        
        if not self.webhook_url:
            print("❌ Error: No webhook URL configured for Teams alerts")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload.dict(),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Teams alert sent successfully: {payload.title}")
                return True
            else:
                print(f"❌ Failed to send Teams alert. Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Teams alert: {e}")
            return False
    
    def sla_breach_alert(self, 
                         metric_name: str, 
                         current_value: float, 
                         threshold: float, 
                         assay_type: str = None,
                         machine_id: str = None,
                         specimen_count: int = None) -> bool:
        """
        Send SLA breach alert.
        
        Args:
            metric_name: Name of the breached metric (e.g., "TAT", "Error Rate")
            current_value: Current value that breached the threshold
            threshold: Threshold value that was exceeded
            assay_type: Type of assay affected (optional)
            machine_id: Machine ID affected (optional)
            specimen_count: Number of specimens affected (optional)
            
        Returns:
            True if alert sent successfully
        """
        # Determine alert severity and color
        if metric_name.lower() in ['tat', 'turnaround time']:
            severity = "HIGH" if current_value > threshold * 1.5 else "MEDIUM"
            color = "#FF0000" if severity == "HIGH" else "#FFA500"
        else:
            severity = "HIGH"
            color = "#FF0000"
        
        # Build alert message
        title = f"🚨 SLA Breach Alert: {metric_name}"
        summary = f"{metric_name} threshold exceeded - {severity} priority"
        
        text = f"""
**SLA Breach Detected**

**Metric:** {metric_name}
**Current Value:** {current_value:.2f}
**Threshold:** {threshold:.2f}
**Severity:** {severity}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Add context if available
        if assay_type:
            text += f"\n**Assay Type:** {assay_type}"
        if machine_id:
            text += f"\n**Machine ID:** {machine_id}"
        if specimen_count:
            text += f"\n**Specimens Affected:** {specimen_count}"
        
        # Create payload
        payload = AlertPayload(
            title=title,
            summary=summary,
            text=text,
            theme_color=color,
            sections=[
                {
                    "activityTitle": f"SLA Breach: {metric_name}",
                    "activitySubtitle": f"Threshold: {threshold:.2f} | Current: {current_value:.2f}",
                    "facts": [
                        {"name": "Metric", "value": metric_name},
                        {"name": "Current Value", "value": f"{current_value:.2f}"},
                        {"name": "Threshold", "value": f"{threshold:.2f}"},
                        {"name": "Severity", "value": severity},
                        {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ]
                }
            ],
            potential_action=[
                {
                    "@type": "OpenUri",
                    "name": "View Dashboard",
                    "targets": [
                        {"os": "default", "uri": "https://labops-metrics-starter-kit.streamlit.app"}
                    ]
                }
            ]
        )
        
        return self.send_alert(payload)
    
    def throughput_alert(self, 
                        current_throughput: int, 
                        target_throughput: int, 
                        time_period: str = "hour") -> bool:
        """
        Send throughput alert when below target.
        
        Args:
            current_throughput: Current throughput value
            target_throughput: Target throughput value
            time_period: Time period for throughput (hour, day, week)
            
        Returns:
            True if alert sent successfully
        """
        if current_throughput >= target_throughput:
            return True  # No alert needed
        
        title = f"📉 Throughput Alert: Below Target"
        summary = f"Current {time_period}ly throughput below target"
        
        text = f"""
**Throughput Below Target**

**Current {time_period.capitalize()}ly Throughput:** {current_throughput}
**Target {time_period.capitalize()}ly Throughput:** {target_throughput}
**Gap:** {target_throughput - current_throughput}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        payload = AlertPayload(
            title=title,
            summary=summary,
            text=text,
            theme_color="#FFA500",  # Orange for warnings
            sections=[
                {
                    "activityTitle": f"Throughput Alert: {time_period.capitalize()}ly",
                    "activitySubtitle": f"Target: {target_throughput} | Current: {current_throughput}",
                    "facts": [
                        {"name": "Current Throughput", "value": str(current_throughput)},
                        {"name": "Target Throughput", "value": str(target_throughput)},
                        {"name": "Gap", "value": str(target_throughput - current_throughput)},
                        {"name": "Time Period", "value": time_period.capitalize()},
                        {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ]
                }
            ]
        )
        
        return self.send_alert(payload)
    
    def error_rate_alert(self, 
                        error_rate: float, 
                        threshold: float, 
                        machine_id: str = None,
                        error_codes: list = None) -> bool:
        """
        Send error rate alert when above threshold.
        
        Args:
            error_rate: Current error rate percentage
            threshold: Error rate threshold percentage
            machine_id: Machine ID with high error rate (optional)
            error_codes: List of error codes (optional)
            
        Returns:
            True if alert sent successfully
        """
        if error_rate <= threshold:
            return True  # No alert needed
        
        title = f"⚠️ Error Rate Alert: Above Threshold"
        summary = f"Error rate {error_rate:.1f}% exceeds threshold {threshold:.1f}%"
        
        text = f"""
**Error Rate Above Threshold**

**Current Error Rate:** {error_rate:.1f}%
**Threshold:** {threshold:.1f}%
**Excess:** {error_rate - threshold:.1f}%
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        if machine_id:
            text += f"\n**Machine ID:** {machine_id}"
        if error_codes:
            text += f"\n**Error Codes:** {', '.join(error_codes)}"
        
        payload = AlertPayload(
            title=title,
            summary=summary,
            text=text,
            theme_color="#FF0000",  # Red for errors
            sections=[
                {
                    "activityTitle": "Error Rate Alert",
                    "activitySubtitle": f"Threshold: {threshold:.1f}% | Current: {error_rate:.1f}%",
                    "facts": [
                        {"name": "Current Error Rate", "value": f"{error_rate:.1f}%"},
                        {"name": "Threshold", "value": f"{threshold:.1f}%"},
                        {"name": "Excess", "value": f"{error_rate - threshold:.1f}%"},
                        {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ]
                }
            ]
        )
        
        return self.send_alert(payload)


def create_sample_teams_payload() -> Dict[str, Any]:
    """Create a sample Teams payload for testing."""
    return {
        "title": "🧪 LabOps Metrics Alert",
        "summary": "Sample alert from LabOps Metrics Starter Kit",
        "text": "This is a sample Teams alert payload for demonstration purposes.",
        "theme_color": "#667eea",
        "sections": [
            {
                "activityTitle": "Sample Alert",
                "activitySubtitle": "LabOps Metrics Starter Kit",
                "facts": [
                    {"name": "System", "value": "LabOps Metrics"},
                    {"name": "Alert Type", "value": "Sample"},
                    {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                ]
            }
        ]
    }


# Example usage and testing
if __name__ == "__main__":
    # Test the notifier
    notifier = TeamsNotifier(dry_run=True)
    
    # Test SLA breach alert
    notifier.sla_breach_alert(
        metric_name="TAT",
        current_value=12.5,
        threshold=8.0,
        assay_type="Blood Chemistry",
        machine_id="MACHINE_001",
        specimen_count=25
    )
    
    # Test throughput alert
    notifier.throughput_alert(
        current_throughput=45,
        target_throughput=60,
        time_period="hour"
    )
    
    # Test error rate alert
    notifier.error_rate_alert(
        error_rate=8.5,
        threshold=5.0,
        machine_id="MACHINE_002",
        error_codes=["E001", "E003"]
    )
    
    print("\n✅ All Teams alert tests completed (dry-run mode)")
