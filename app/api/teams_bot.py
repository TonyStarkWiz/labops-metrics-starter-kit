#!/usr/bin/env python3
"""
Microsoft Teams Stand-up Bot API endpoints
Integrates the Teams stand-up bot with FastAPI
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

# Import the Teams stand-up bot
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
from teams_standup_bot import TeamsStandupBot, StandupUpdate, StandupItem

router = APIRouter()

@router.post("/standup/post")
async def post_standup_update(
    standup_data: Dict[str, Any],
    webhook_url: Optional[str] = Form(None),
    dry_run: bool = Form(False)
):
    """
    Post a stand-up update to Teams
    
    Args:
        standup_data: Stand-up data in JSON format
        webhook_url: Teams webhook URL (optional, can use env var)
        dry_run: If True, don't actually post to Teams
    """
    try:
        # Parse stand-up data
        update = StandupUpdate(
            date=standup_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            team_member=standup_data['team_member'],
            items=[
                StandupItem(
                    title=item['title'],
                    status=item['status'],
                    description=item['description'],
                    assignee=item['assignee'],
                    priority=item.get('priority', 'medium'),
                    effort=item.get('effort', '1-2h'),
                    blockers=item.get('blockers', []),
                    notes=item.get('notes', '')
                )
                for item in standup_data.get('items', [])
            ],
            mood=standup_data.get('mood', '😊'),
            availability=standup_data.get('availability', 'Available'),
            next_priorities=standup_data.get('next_priorities', [])
        )
        
        # Initialize bot
        bot = TeamsStandupBot(
            webhook_url=webhook_url or os.getenv('TEAMS_WEBHOOK_URL'),
            dry_run=dry_run
        )
        
        # Post stand-up
        success = bot.post_standup(update)
        
        if success:
            return {
                "status": "success",
                "message": "Stand-up posted successfully",
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to post stand-up to Teams")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error posting stand-up: {str(e)}")

@router.post("/standup/team-post")
async def post_team_standup(
    team_data: Dict[str, Any],
    webhook_url: Optional[str] = Form(None),
    dry_run: bool = Form(False)
):
    """
    Post a team-wide stand-up update to Teams
    
    Args:
        team_data: Team stand-up data with multiple members
        webhook_url: Teams webhook URL (optional, can use env var)
        dry_run: If True, don't actually post to Teams
    """
    try:
        # Parse team stand-up data
        updates = []
        for member_data in team_data.get('team_members', []):
            update = StandupUpdate(
                date=member_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                team_member=member_data['team_member'],
                items=[
                    StandupItem(
                        title=item['title'],
                        status=item['status'],
                        description=item['description'],
                        assignee=item['assignee'],
                        priority=item.get('priority', 'medium'),
                        effort=item.get('effort', '1-2h'),
                        blockers=item.get('blockers', []),
                        notes=item.get('notes', '')
                    )
                    for item in member_data.get('items', [])
                ],
                mood=member_data.get('mood', '😊'),
                availability=member_data.get('availability', 'Available'),
                next_priorities=member_data.get('next_priorities', [])
            )
            updates.append(update)
        
        # Initialize bot
        bot = TeamsStandupBot(
            webhook_url=webhook_url or os.getenv('TEAMS_WEBHOOK_URL'),
            dry_run=dry_run
        )
        
        # Post team stand-up
        success = bot.post_team_standup(updates)
        
        if success:
            return {
                "status": "success",
                "message": f"Team stand-up posted successfully for {len(updates)} members",
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to post team stand-up to Teams")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error posting team stand-up: {str(e)}")

@router.post("/standup/upload-json")
async def post_standup_from_json(
    file: UploadFile = File(...),
    webhook_url: Optional[str] = Form(None),
    dry_run: bool = Form(False)
):
    """
    Post stand-up from uploaded JSON file
    
    Args:
        file: JSON file with stand-up data
        webhook_url: Teams webhook URL (optional, can use env var)
        dry_run: If True, don't actually post to Teams
    """
    try:
        # Read JSON data
        content = await file.read()
        standup_data = json.loads(content.decode())
        
        # Initialize bot
        bot = TeamsStandupBot(
            webhook_url=webhook_url or os.getenv('TEAMS_WEBHOOK_URL'),
            dry_run=dry_run
        )
        
        # Handle single or team stand-up
        if 'team_members' in standup_data:
            # Team stand-up
            updates = []
            for member_data in standup_data['team_members']:
                update = StandupUpdate(
                    date=member_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                    team_member=member_data['team_member'],
                    items=[
                        StandupItem(
                            title=item['title'],
                            status=item['status'],
                            description=item['description'],
                            assignee=item['assignee'],
                            priority=item.get('priority', 'medium'),
                            effort=item.get('effort', '1-2h'),
                            blockers=item.get('blockers', []),
                            notes=item.get('notes', '')
                        )
                        for item in member_data.get('items', [])
                    ],
                    mood=member_data.get('mood', '😊'),
                    availability=member_data.get('availability', 'Available'),
                    next_priorities=member_data.get('next_priorities', [])
                )
                updates.append(update)
            
            success = bot.post_team_standup(updates)
            message = f"Team stand-up posted for {len(updates)} members"
        else:
            # Single stand-up
            update = StandupUpdate(
                date=standup_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                team_member=standup_data['team_member'],
                items=[
                    StandupItem(
                        title=item['title'],
                        status=item['status'],
                        description=item['description'],
                        assignee=item['assignee'],
                        priority=item.get('priority', 'medium'),
                        effort=item.get('effort', '1-2h'),
                        blockers=item.get('blockers', []),
                        notes=item.get('notes', '')
                    )
                    for item in standup_data.get('items', [])
                ],
                mood=standup_data.get('mood', '😊'),
                availability=standup_data.get('availability', 'Available'),
                next_priorities=standup_data.get('next_priorities', [])
            )
            
            success = bot.post_standup(update)
            message = "Stand-up posted successfully"
        
        if success:
            return {
                "status": "success",
                "message": message,
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to post stand-up to Teams")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing JSON file: {str(e)}")

@router.get("/standup/templates")
async def get_standup_templates():
    """Get stand-up templates and examples"""
    return {
        "single_standup_template": {
            "date": "2024-01-15",
            "team_member": "John Doe",
            "items": [
                {
                    "title": "Complete API documentation",
                    "status": "completed",
                    "description": "Write comprehensive API docs",
                    "assignee": "John Doe",
                    "priority": "high",
                    "effort": "4h",
                    "notes": "Ready for review"
                },
                {
                    "title": "Fix authentication bug",
                    "status": "in_progress",
                    "description": "Investigate login issues",
                    "assignee": "John Doe",
                    "priority": "urgent",
                    "effort": "2h",
                    "blockers": ["Need access to logs"]
                }
            ],
            "mood": "😊",
            "availability": "Available",
            "next_priorities": ["Code review", "Team meeting"]
        },
        "team_standup_template": {
            "team_members": [
                {
                    "date": "2024-01-15",
                    "team_member": "John Doe",
                    "items": [
                        {
                            "title": "API documentation",
                            "status": "completed",
                            "description": "Write API docs",
                            "assignee": "John Doe",
                            "priority": "high",
                            "effort": "4h"
                        }
                    ],
                    "mood": "😊",
                    "availability": "Available"
                },
                {
                    "date": "2024-01-15",
                    "team_member": "Jane Smith",
                    "items": [
                        {
                            "title": "Database optimization",
                            "status": "in_progress",
                            "description": "Optimize query performance",
                            "assignee": "Jane Smith",
                            "priority": "medium",
                            "effort": "6h"
                        }
                    ],
                    "mood": "🤔",
                    "availability": "Available"
                }
            ]
        },
        "status_options": ["completed", "in_progress", "blocked", "planned"],
        "priority_options": ["low", "medium", "high", "urgent"],
        "effort_options": ["15m", "30m", "1h", "2h", "4h", "6h", "8h", "1d"]
    }

@router.get("/health")
async def teams_bot_health():
    """Health check for Teams bot"""
    webhook_configured = bool(os.getenv('TEAMS_WEBHOOK_URL'))
    
    return {
        "status": "healthy",
        "service": "Microsoft Teams Stand-up Bot",
        "webhook_configured": webhook_configured,
        "timestamp": datetime.now().isoformat()
    }
