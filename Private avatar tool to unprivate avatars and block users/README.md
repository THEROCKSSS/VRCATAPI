# VRChat Management Tools

This repository contains two Python tools for managing VRChat avatars and user blocks:

## 1. Avatar Privacy Manager (avatar_privacy_manager.py)

A tool to manage the privacy settings of your VRChat avatars, allowing you to easily switch avatars between public and private states.

### Features:
- List all your avatars with their current privacy status
- Toggle avatar privacy between public and private
- Shows avatar IDs and status with visual indicators (🔒 private, 🌐 public)

### Setup:
1. Install the required package:
```powershell
pip install vrchatapi
```

2. Make sure you have the `block_manager.py` file in the same directory (it's used for authentication)

### Usage:
Run the script:
```powershell
python avatar_privacy_manager.py
```

The tool will present a menu with the following options:
1. List all my avatars
2. Toggle avatar privacy (private/public)
3. Exit

When toggling privacy:
- A list of your avatars will be shown with numbers
- Enter the number of the avatar you want to modify
- The tool will automatically toggle between private and public status

Note: Some avatars might fail to update if they have invalid file extensions or weren't uploaded with the correct Unity version.

## 2. Block Manager (block_manager.py)

A tool to manage your VRChat blocked users list, with the ability to save blocked user IDs to a file and bulk block/unblock users.

### Features:
- Block individual users by ID
- Unblock individual users by ID
- List all currently blocked users
- Bulk block users from a file
- Bulk unblock users from a file
- Save blocked user IDs to a file for later use
- Session cookie management for faster subsequent logins

### Setup:
1. Install the required package:
```powershell
pip install vrchatapi
```

2. The script will automatically create a `usrids.txt` file if it doesn't exist
3. The script will manage cookies in `vrchat_cookies.json`

### Usage:
Run the script:
```powershell
python block_manager.py
```

The tool will present a menu with the following options:
1. Block User by ID
2. Unblock User by ID
3. List Blocked Users
4. Block All Users from File
5. Unblock All Users from File
6. List Users in File
7. Exit

### File Management:
- Blocked users are stored in `usrids.txt`
- One user ID per line
- The file is automatically created if it doesn't exist
- User IDs are automatically added to the file when blocking users

### Authentication:
Both tools use the same authentication system that:
- Supports 2FA and email 2FA
- Saves cookies for faster subsequent logins
- Will prompt for credentials if cookies are invalid or missing

## Requirements
- Python 3.6 or higher
- vrchatapi package
- Internet connection
- Valid VRChat account

## Security Notes
- Your VRChat cookies are stored locally in `vrchat_cookies.json`
- Your user credentials are never stored, only session cookies
- Always keep your `vrchat_cookies.json` file private and secure

## Troubleshooting
1. If you get login errors:
   - Delete `vrchat_cookies.json` and try again
   - Make sure your credentials are correct
   - Check your internet connection

2. If avatar privacy updates fail:
   - Make sure you own the avatar
   - Check if the avatar was uploaded with a supported Unity version
   - Some avatars might need to be reuploaded through the VRChat SDK
