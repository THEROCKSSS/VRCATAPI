# VRChat Avatar Information Fetcher

## Setup Instructions

1. **Install Requirements**:
   ```bash
   pip install vrchatapi requests
   ```

2. **Configuration**:
   - Edit `config.json`:
     ```json
     {
       "discord": {
         "enabled": true,
         "webhooks": ["your_webhook_url_here"]
       },
       "vrchat": {
         "rate_limit_delay": 5
       }
     }
     ```
   - Add avatar IDs to `avatar_ids.txt` (one per line)

3. **Running in VS Code**:
   - Open the project folder in VS Code
   - Run from terminal:
     ```bash
     python "Python scripts/avatar_info.py"
     ```
     
## File Descriptions
- `avatar_ids.txt` - List of avatar IDs to check
- `discord_avatar_check.txt` - Tracks processed avatars
- `config.json` - Configuration settings