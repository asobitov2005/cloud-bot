"""
Permission system for admin users
"""
import json
from typing import List, Optional

# Available permissions
PERMISSIONS = {
    "upload": "Upload Files",
    "delete": "Delete Files",
    "stats": "View Statistics",
    "users": "Manage Users",
    "broadcast": "Send Broadcasts",
    "settings": "Manage Settings",
    "fsub": "Manage Force Join Channels"
}

ALL_PERMISSIONS = list(PERMISSIONS.keys())


def parse_permissions(permissions_str: Optional[str]) -> List[str]:
    """Parse permissions from JSON string"""
    if not permissions_str:
        return []
    try:
        return json.loads(permissions_str)
    except (json.JSONDecodeError, TypeError):
        return []


def serialize_permissions(permissions: List[str]) -> str:
    """Serialize permissions to JSON string"""
    return json.dumps(permissions)


def has_permission(permissions_str: Optional[str], permission: str) -> bool:
    """Check if user has a specific permission"""
    permissions = parse_permissions(permissions_str)
    return permission in permissions


def get_permission_display_names(permissions: List[str]) -> List[str]:
    """Get display names for permissions"""
    return [PERMISSIONS.get(p, p) for p in permissions]

