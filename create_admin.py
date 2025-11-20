"""
Create or update admin credentials for the web panel.
This script updates the .env file with admin credentials.
"""
import sys
import os
from pathlib import Path

def create_admin(username, password):
    env_path = Path('.env')
    
    # Read existing .env
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add admin credentials
    updated = False
    admin_user_found = False
    admin_pass_found = False
    
    for i, line in enumerate(lines):
        if line.startswith('ADMIN_USERNAME='):
            lines[i] = f'ADMIN_USERNAME={username}\n'
            admin_user_found = True
        elif line.startswith('ADMIN_PASSWORD='):
            lines[i] = f'ADMIN_PASSWORD={password}\n'
            admin_pass_found = True
    
    # Add if not found
    if not admin_user_found:
        lines.append(f'ADMIN_USERNAME={username}\n')
    if not admin_pass_found:
        lines.append(f'ADMIN_PASSWORD={password}\n')
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✓ Admin credentials updated in .env file")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"\nPlease restart the application for changes to take effect.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)
        
    username = sys.argv[1]
    password = sys.argv[2]
    
    create_admin(username, password)
