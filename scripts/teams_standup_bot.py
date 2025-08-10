#!/usr/bin/env python3
"""
Microsoft Teams Stand-up Bot for LabOps Metrics
Reads GitHub issues or local JSON and posts stand-up updates to Teams channels
"""

import json
import os
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from pathlib import Path
import yaml
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class StandupItem:
    """Individual stand-up item"""
    title: str
    status: str  # "completed", "in_progress", "blocked", "planned"
    description: str
    assignee: str
    priority: str = "medium"  # "low", "medium", "high", "urgent"
    effort: str = "1-2h"  # estimated effort
    blockers: List[str] = None
    notes: str = ""

@dataclass
class StandupUpdate:
    """Complete stand-up update"""
    date: str
    team_member: str
    items: List[StandupItem]
    mood: str = "😊"  # emoji mood indicator
    availability: str = "Available"
    next_priorities: List[str] = None

class TeamsStandupBot:
    """Microsoft Teams Stand-up Bot for posting updates"""
    
    def __init__(self, webhook_url: Optional[str] = None, dry_run: bool = True):
        self.webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
        self.dry_run = dry_run
        
        if not self.webhook_url and not dry_run:
            print("Warning: No Teams webhook URL provided. Use --webhook or set TEAMS_WEBHOOK_URL env var.")
    
    def create_standup_payload(self, update: StandupUpdate) -> Dict[str, Any]:
        """Create Teams message card payload for stand-up update"""
        
        # Group items by status
        completed = [item for item in update.items if item.status == "completed"]
        in_progress = [item for item in update.items if item.status == "in_progress"]
        blocked = [item for item in update.items if item.status == "blocked"]
        planned = [item for item in update.items if item.status == "planned"]
        
        # Create sections
        sections = []
        
        # Completed items
        if completed:
            completed_text = "\n".join([
                f"✅ **{item.title}** ({item.effort})" + 
                (f" - {item.notes}" if item.notes else "")
                for item in completed
            ])
            sections.append({
                "activityTitle": "🎯 Completed Today",
                "text": completed_text
            })
        
        # In progress items
        if in_progress:
            in_progress_text = "\n".join([
                f"🔄 **{item.title}** ({item.effort})" + 
                (f" - {item.notes}" if item.notes else "")
                for item in in_progress
            ])
            sections.append({
                "activityTitle": "🚧 In Progress",
                "text": in_progress_text
            })
        
        # Blocked items
        if blocked:
            blocked_text = "\n".join([
                f"🚫 **{item.title}** - Blockers: {', '.join(item.blockers or [])}" +
                (f" - {item.notes}" if item.notes else "")
                for item in blocked
            ])
            sections.append({
                "activityTitle": "🚫 Blocked",
                "text": blocked_text
            })
        
        # Planned items
        if planned:
            planned_text = "\n".join([
                f"📋 **{item.title}** ({item.effort})" +
                (f" - {item.notes}" if item.notes else "")
                for item in planned
            ])
            sections.append({
                "activityTitle": "📋 Planned Next",
                "text": planned_text
            })
        
        # Next priorities
        if update.next_priorities:
            priorities_text = "\n".join([f"• {priority}" for priority in update.next_priorities])
            sections.append({
                "activityTitle": "🎯 Next Priorities",
                "text": priorities_text
            })
        
        # Create the message card
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": self._get_theme_color(update),
            "summary": f"Stand-up Update: {update.team_member} - {update.date}",
            "sections": [
                {
                    "activityTitle": f"{update.mood} {update.team_member}'s Stand-up Update",
                    "activitySubtitle": f"📅 {update.date} | 🕐 {datetime.now().strftime('%H:%M')}",
                    "text": f"**Availability:** {update.availability}"
                }
            ] + sections
        }
        
        return payload
    
    def _get_theme_color(self, update: StandupUpdate) -> str:
        """Get theme color based on update content"""
        if any(item.status == "blocked" for item in update.items):
            return "#FF0000"  # Red for blocked items
        elif any(item.status == "in_progress" for item in update.items):
            return "#FFA500"  # Orange for in-progress
        else:
            return "#00FF00"  # Green for all completed/planned
    
    def post_standup(self, update: StandupUpdate) -> bool:
        """Post stand-up update to Teams"""
        payload = self.create_standup_payload(update)
        
        if self.dry_run:
            print("🔔 DRY RUN - Stand-up update would be posted:")
            print(json.dumps(payload, indent=2, default=str))
            return True
        
        if not self.webhook_url:
            print("❌ No webhook URL available")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Stand-up update posted successfully!")
                return True
            else:
                print(f"❌ Failed to post update: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error posting update: {e}")
            return False
    
    def post_team_standup(self, updates: List[StandupUpdate]) -> bool:
        """Post team-wide stand-up summary"""
        if not updates:
            print("No updates to post")
            return False
        
        # Create team summary
        team_members = [update.team_member for update in updates]
        total_items = sum(len(update.items) for update in updates)
        completed_items = sum(len([item for item in update.items if item.status == "completed"]) for update in updates)
        blocked_items = sum(len([item for item in update.items if item.status == "blocked"]) for update in updates)
        
        # Create team payload
        team_payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "#667eea",
            "summary": f"Team Stand-up Summary - {datetime.now().strftime('%Y-%m-%d')}",
            "sections": [
                {
                    "activityTitle": "👥 Team Stand-up Summary",
                    "activitySubtitle": f"📅 {datetime.now().strftime('%Y-%m-%d')} | 🕐 {datetime.now().strftime('%H:%M')}",
                    "text": f"**Team Members:** {', '.join(team_members)}\n**Total Items:** {total_items}\n**Completed:** {completed_items}\n**Blocked:** {blocked_items}"
                }
            ]
        }
        
        # Add individual updates as expandable sections
        for update in updates:
            update_summary = f"**{update.team_member}** ({update.mood})\n"
            update_summary += f"Completed: {len([item for item in update.items if item.status == 'completed'])}\n"
            update_summary += f"In Progress: {len([item for item in update.items if item.status == 'in_progress'])}\n"
            update_summary += f"Blocked: {len([item for item in update.items if item.status == 'blocked'])}"
            
            team_payload["sections"].append({
                "activityTitle": f"👤 {update.team_member}",
                "text": update_summary
            })
        
        if self.dry_run:
            print("🔔 DRY RUN - Team stand-up summary would be posted:")
            print(json.dumps(team_payload, indent=2, default=str))
            return True
        
        if not self.webhook_url:
            print("❌ No webhook URL available")
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=team_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Team stand-up summary posted successfully!")
                return True
            else:
                print(f"❌ Failed to post team summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error posting team summary: {e}")
            return False

def load_standup_data(data_file: str) -> List[StandupUpdate]:
    """Load stand-up data from JSON or YAML file"""
    file_path = Path(data_file)
    
    if not file_path.exists():
        print(f"Error: Data file '{data_file}' not found")
        return []
    
    try:
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            with open(file_path, 'r') as f:
                data = json.load(f)
        
        # Convert to StandupUpdate objects
        updates = []
        for item in data.get('standup_updates', []):
            items = []
            for task in item.get('items', []):
                items.append(StandupItem(
                    title=task['title'],
                    status=task['status'],
                    description=task.get('description', ''),
                    assignee=task.get('assignee', 'Unknown'),
                    priority=task.get('priority', 'medium'),
                    effort=task.get('effort', '1-2h'),
                    blockers=task.get('blockers', []),
                    notes=task.get('notes', '')
                ))
            
            updates.append(StandupUpdate(
                date=item.get('date', datetime.now().strftime('%Y-%m-%d')),
                team_member=item['team_member'],
                items=items,
                mood=item.get('mood', '😊'),
                availability=item.get('availability', 'Available'),
                next_priorities=item.get('next_priorities', [])
            ))
        
        return updates
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

def create_sample_standup_data() -> Dict[str, Any]:
    """Create sample stand-up data"""
    return {
        "standup_updates": [
            {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "team_member": "Alice Johnson",
                "mood": "😊",
                "availability": "Available",
                "items": [
                    {
                        "title": "Implement TAT metrics calculation",
                        "status": "completed",
                        "description": "Added P50/P90/P99 calculations for turnaround time",
                        "assignee": "Alice",
                        "priority": "high",
                        "effort": "4h",
                        "notes": "Ready for testing"
                    },
                    {
                        "title": "Fix SLA breach detection",
                        "status": "in_progress",
                        "description": "Debugging threshold comparison logic",
                        "assignee": "Alice",
                        "priority": "high",
                        "effort": "2h",
                        "notes": "Found the issue, implementing fix"
                    },
                    {
                        "title": "Add error rate metrics",
                        "status": "planned",
                        "description": "Calculate error rates by machine and error code",
                        "assignee": "Alice",
                        "priority": "medium",
                        "effort": "3h"
                    }
                ],
                "next_priorities": [
                    "Complete SLA breach fix",
                    "Test error rate calculations",
                    "Update documentation"
                ]
            },
            {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "team_member": "Bob Smith",
                "mood": "🤔",
                "availability": "Available (after 2pm)",
                "items": [
                    {
                        "title": "Streamlit dashboard optimization",
                        "status": "completed",
                        "description": "Reduced loading time from 30s to 5s",
                        "assignee": "Bob",
                        "priority": "medium",
                        "effort": "3h",
                        "notes": "Performance improved significantly"
                    },
                    {
                        "title": "Power BI export script",
                        "status": "blocked",
                        "description": "Waiting for data format specification",
                        "assignee": "Bob",
                        "priority": "high",
                        "effort": "4h",
                        "blockers": ["Data format not finalized", "Waiting for stakeholder approval"],
                        "notes": "Need clarification on requirements"
                    },
                    {
                        "title": "Add data validation rules",
                        "status": "planned",
                        "description": "Implement data quality checks",
                        "assignee": "Bob",
                        "priority": "medium",
                        "effort": "2h"
                    }
                ],
                "next_priorities": [
                    "Resolve Power BI export blockers",
                    "Implement data validation",
                    "Code review for dashboard changes"
                ]
            }
        ]
    }

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Microsoft Teams Stand-up Bot for LabOps Metrics")
    parser.add_argument("--data", "-d", help="Path to stand-up data file (JSON/YAML)")
    parser.add_argument("--webhook", "-w", help="Teams webhook URL")
    parser.add_argument("--team", "-t", action="store_true", help="Post team summary instead of individual updates")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show what would be posted without actually posting")
    parser.add_argument("--create-sample", action="store_true", help="Create sample stand-up data file")
    
    args = parser.parse_args()
    
    # Create sample data if requested
    if args.create_sample:
        sample_file = "sample_standup_data.json"
        with open(sample_file, 'w') as f:
            json.dump(create_sample_standup_data(), f, indent=2, default=str)
        print(f"Sample stand-up data created: {sample_file}")
        return
    
    # Initialize bot
    bot = TeamsStandupBot(
        webhook_url=args.webhook,
        dry_run=args.dry_run
    )
    
    # Load data
    if args.data:
        updates = load_standup_data(args.data)
        if not updates:
            print("No valid stand-up data found")
            sys.exit(1)
    else:
        print("No data file specified, using sample data")
        sample_data = create_sample_standup_data()
        updates = load_standup_data_from_dict(sample_data)
    
    print(f"Loaded {len(updates)} stand-up updates")
    
    # Post updates
    if args.team:
        print("Posting team stand-up summary...")
        success = bot.post_team_standup(updates)
    else:
        print("Posting individual stand-up updates...")
        success = True
        for update in updates:
            print(f"\nPosting update for {update.team_member}...")
            if not bot.post_standup(update):
                success = False
    
    if success:
        print("\n✅ All updates posted successfully!")
    else:
        print("\n❌ Some updates failed to post")
        sys.exit(1)

def load_standup_data_from_dict(data: Dict[str, Any]) -> List[StandupUpdate]:
    """Load stand-up data from dictionary (for sample data)"""
    updates = []
    for item in data.get('standup_updates', []):
        items = []
        for task in item.get('items', []):
            items.append(StandupItem(
                title=task['title'],
                status=task['status'],
                description=task.get('description', ''),
                assignee=task.get('assignee', 'Unknown'),
                priority=task.get('priority', 'medium'),
                effort=task.get('effort', '1-2h'),
                blockers=task.get('blockers', []),
                notes=task.get('notes', '')
            ))
        
        updates.append(StandupUpdate(
            date=item.get('date', datetime.now().strftime('%Y-%m-%d')),
            team_member=item['team_member'],
            items=items,
            mood=item.get('mood', '😊'),
            availability=item.get('availability', 'Available'),
            next_priorities=item.get('next_priorities', [])
        ))
    
    return updates

if __name__ == "__main__":
    main()
