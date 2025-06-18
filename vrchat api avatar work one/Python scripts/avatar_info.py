import vrchatapi
import json
from vrchatapi.api import authentication_api, avatars_api
from vrchatapi.exceptions import ApiException, UnauthorizedException
import time
import sys
import os
import requests
from http.cookiejar import Cookie

def make_cookie(name, value):
    """Helper to create cookie objects"""
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain="api.vrchat.cloud",
        domain_specified=True,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=False,
        expires=None,
        discard=False,
        comment=None,
        comment_url=None,
        rest={}
    )

def load_cookies(api_client):
    """Try loading cookies from file if they exist"""
    cookie_file = os.path.join(os.path.dirname(__file__), 'vrchat_cookies.json')
    if not os.path.exists(cookie_file):
        return False
        
    try:
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
            
        for name, value in cookies.items():
            api_client.rest_client.cookie_jar.set_cookie(
                make_cookie(name, value)
            )
        return True
    except Exception as e:
        print(f"[!] Error loading cookies: {str(e)}")
        return False

def save_cookies(api_client):
    """Save cookies to file for future use"""
    cookie_file = os.path.join(os.path.dirname(__file__), 'vrchat_cookies.json')
    try:
        cookies = {
            cookie.name: cookie.value
            for cookie in api_client.rest_client.cookie_jar
            if cookie.domain == "api.vrchat.cloud"
        }
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)
        return True
    except Exception as e:
        print(f"[!] Error saving cookies: {str(e)}")
        return False

def login():
    while True:
        try:
            print("\nVRChat Login")
            print("============")
            username = input("Enter your VRChat username/email: ")
            password = input("Enter your VRChat password: ")

            configuration = vrchatapi.Configuration(
                username=username,
                password=password
            )

            api_client = vrchatapi.ApiClient(configuration)
            api_client.user_agent = "AvatarInfoFetcher/1.0.0"
            
            # Try loading cookies first
            if load_cookies(api_client):
                print("\n[✓] Loaded saved cookies - attempting session reuse")
            
            auth_api = authentication_api.AuthenticationApi(api_client)

            try:
                current_user = auth_api.get_current_user()
                print(f"\nLogged in as: {current_user.display_name}")
                save_cookies(api_client)  # Save cookies after successful login
                return api_client

            except UnauthorizedException as e:
                if "2 Factor Authentication" in str(e) or "Email 2 Factor Authentication" in str(e):
                    code = input("2FA Code: ")
                    if "Email" in str(e):
                        auth_api.verify2_fa_email_code({"code": code})
                    else:
                        auth_api.verify2_fa({"code": code})
                    current_user = auth_api.get_current_user()
                    print(f"\nLogged in as: {current_user.display_name}")
                    save_cookies(api_client)  # Save cookies after successful 2FA
                    return api_client
                else:
                    print(f"\nError: {str(e)}")

        except ApiException as e:
            print(f"\nError during login: {str(e)}")
            
        retry = input("\nWould you like to try again? (y/n): ")
        if retry.lower() != 'y':
            sys.exit(1)

def read_avatar_ids(filename):
    try:
        with open(filename, 'r') as f:
            avatar_ids = [line.strip() for line in f if line.strip()]
            if not avatar_ids:
                print(f"Warning: {filename} is empty")
                print("Please add avatar IDs (one per line)")
                sys.exit(1)
            return avatar_ids
    except FileNotFoundError:
        print(f"Error: {filename} not found in script directory")
        print("Creating empty file...")
        with open(filename, 'w') as f:
            f.write("# Add avatar IDs here, one per line\n")
        print(f"Created {filename} - please add avatar IDs and run again")
        sys.exit(1)

def is_avatar_processed(avatar_id):
    """Check if avatar ID exists in processed log file"""
    check_file = os.path.join(os.path.dirname(__file__), 'discord_avatar_check.txt')
    if not os.path.exists(check_file):
        return False
    with open(check_file, 'r') as f:
        return avatar_id in [line.strip() for line in f if line.strip() and not line.startswith('#')]

def log_processed_avatar(avatar_id):
    """Add avatar ID to processed log file"""
    check_file = os.path.join(os.path.dirname(__file__), 'discord_avatar_check.txt')
    with open(check_file, 'a') as f:
        f.write(f"{avatar_id}\n")

def get_avatar_info(avatars_api_instance, avatar_id, discord_webhooks=None, rate_limit_delay=5):
    # Skip API call if already processed
    if is_avatar_processed(avatar_id):
        print(f"\nAvatar {avatar_id} already processed - skipping API call")
        return {
            'id': avatar_id,
            'status': 'processed',
            'message': 'Already sent to Discord'
        }
        
    try:
        avatar = avatars_api_instance.get_avatar(avatar_id)
        
        # Determine platform availability
        platforms = []
        if hasattr(avatar, 'unity_packages') and avatar.unity_packages:
            for package in avatar.unity_packages:
                if hasattr(package, 'platform'):
                    if package.platform == "standalonewindows":
                        platforms.append("PC")
                    elif package.platform == "android":
                        platforms.append("Quest")
        
        platform_status = "PC & Quest" if len(platforms) > 1 else platforms[0] if platforms else "Unknown"
        
        result = {
            'id': avatar_id,
            'name': avatar.name if hasattr(avatar, 'name') and avatar.name else "Unknown Name",
            'author_name': avatar.author_name if hasattr(avatar, 'author_name') else "Unknown Author",
            'release_status': avatar.release_status if hasattr(avatar, 'release_status') else "Unknown Status",
            'description': getattr(avatar, 'description', None) or "No description",
            'image_url': getattr(avatar, 'image_url', None),
            'thumbnail_url': getattr(avatar, 'thumbnail_image_url', None),
            'platform': platform_status,
            'status': 'success'
        }
        
        if discord_webhooks and not is_avatar_processed(avatar_id):
            print(f"\nSending to {len(discord_webhooks)} Discord webhooks...")
            for webhook in discord_webhooks:
                success = send_to_discord(result, webhook)
                if not success:
                    print(f"[!] Failed to send to webhook: {webhook[:60]}...")
                if len(discord_webhooks) > 1:
                    time.sleep(rate_limit_delay)  # Delay between webhook sends
            
        # Log successful processing
        if discord_webhooks:
            log_processed_avatar(avatar_id)
        return result

    except ValueError as ve:
        if "Invalid value for `name`" in str(ve):
            error_msg = f"Avatar {avatar_id} has invalid or missing name"
            print(f"\n[!] {error_msg}")
            if discord_webhooks:
                print(f"\nSending error to {len(discord_webhooks)} Discord webhooks...")
                for webhook in discord_webhooks:
                    success = send_to_discord({
                        'id': avatar_id,
                        'status': 'error',
                        'error': error_msg
                    }, webhook)
                    if not success:
                        print(f"Failed to send error to webhook: {webhook}")
            return {
                'id': avatar_id,
                'status': 'error',
                'error': error_msg
            }
        raise  # Re-raise other ValueError exceptions
        
    except ApiException as e:
        error_msg = f"Avatar {avatar_id} not found or private"
        if discord_webhooks:
            print(f"\nSending error to {len(discord_webhooks)} Discord webhooks...")
            for webhook in discord_webhooks:
                success = send_to_discord({
                'id': avatar_id,
                'status': 'error',
                'error': error_msg
                }, webhook)
                if not success:
                    print(f"Failed to send error to webhook: {webhook}")
        return {
            'id': avatar_id,
            'status': 'error',
            'error': error_msg
        }

def send_to_discord(data, webhook_url):
    # Validate webhook URL format
    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
        print(f"[!] DISCORD ERROR: Invalid webhook URL format")
        return False
    
    # Check if webhook URL contains required components
    parts = webhook_url.split('/')
    if len(parts) < 7 or not parts[5].isnumeric() or len(parts[6]) < 30:
        print(f"[!] DISCORD ERROR: Malformed webhook URL")
        return False
    
    embed = {
        "title": f"Avatar Info: {data.get('id', 'Unknown')}",
        "color": 0x00ff00 if data.get('status') == 'success' else 0xff0000
    }
    
    if data.get('status') == 'success':
        embed["fields"] = [
            {"name": "Name", "value": data['name'], "inline": True},
            {"name": "Author", "value": data['author_name'], "inline": True},
            {"name": "Status", "value": data['release_status'], "inline": True},
            {"name": "Platform", "value": data['platform'], "inline": True},
            {"name": "Description", "value": data['description'], "inline": False}
        ]
        if data.get('image_url'):
            embed["image"] = {"url": data['image_url']}
    else:
        embed["description"] = data.get('error', 'Unknown error')
    
    payload = {
        "embeds": [embed]
    }
    
    max_retries = 3
    attempt = 1
    
    while attempt <= max_retries:
        try:
            print(f"\n[Discord] Sending to webhook (attempt {attempt}/{max_retries})...")
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 204:
                print("[✓] Discord webhook sent successfully")
                return True
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                print(f"[!] RATE LIMITED: Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after)
                attempt += 1
                continue
            else:
                print(f"[!] Discord error (HTTP {response.status_code}): {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[!] Discord connection error: {str(e)}")
            return False
    
    print("[!] Failed to send to Discord after maximum retries")
    return False

def main():
    print("\nVRChat Avatar Information Fetcher")
    print("================================")
    print("Checking configuration...")
    
    # Login
    api_client = login()
    avatars_api_instance = avatars_api.AvatarsApi(api_client)
    
    # Read avatar IDs
    avatar_ids = read_avatar_ids('avatar_ids.txt')
    
    # Load and validate configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    discord_webhooks = []
    discord_enabled = False
    rate_limit_delay = 5  # Default delay between webhook sends
    
    try:
        with open(config_path) as f:
            config = json.load(f)
            
        # Check Discord configuration
        discord_config = config.get('discord', {})
        discord_enabled = discord_config.get('enabled', False)
        rate_limit_delay = config.get('vrchat', {}).get('rate_limit_delay', 5)
        
        if discord_enabled:
            discord_webhooks = discord_config.get('webhooks', [])
            if not discord_webhooks:
                print("\n[!] ERROR: Discord is enabled but no webhooks configured!")
                print("Please add webhook URLs to config.json or set 'enabled': false")
                sys.exit(1)
                
            print("\n[✓] Discord webhooks configured:")
            for i, url in enumerate(discord_webhooks, 1):
                print(f"  {i}. {url[:60]}...")
                
    except FileNotFoundError:
        print("\n[!] ERROR: config.json not found!")
        print("Please create the config file with required settings")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\n[!] ERROR: Invalid config.json format!")
        print("Please check the file is valid JSON")
        sys.exit(1)
    
    if not avatar_ids:
        print("No avatar IDs found in avatar_ids.txt")
        sys.exit(1)
    
    print("\nStarting avatar information fetch...")
    
    for avatar_id in avatar_ids:
        print(f"\nFetching information for avatar: {avatar_id}")
        info = get_avatar_info(avatars_api_instance, avatar_id, discord_webhooks, rate_limit_delay)
        
        if isinstance(info, dict):
            print("\n" + "="*50)
            print(f"Avatar id:{info['id']}")
            
            if info.get('status') == 'error':
                print(f"Error: {info.get('error', 'Unknown error')}")
                print("="*50)
            elif info.get('status') != 'processed':
                try:
                    print(f"Avatar Name: {info['name']}")
                    print(f"Author: {info['author_name']}")
                    print(f"Status: {info['release_status']}")
                    print(f"Platform: {info['platform']}")
                    print(f"Description: {info['description']}")
                    if info.get('image_url'):
                        print(f"Image URL: {info['image_url']}")
                    if info.get('thumbnail_url'):
                        print(f"Thumbnail URL: {info['thumbnail_url']}")
                    print("="*50)
                    
                    # Write to API log file with UTF-8 encoding
                    try:
                        with open('api_log.txt', 'a', encoding='utf-8') as log:
                            log.write("==================================================\n")
                            log.write(f"Avatar id:{info['id']}\n")
                            log.write(f"Avatar Name: {info['name']}\n")
                            log.write(f"Author: {info['author_name']}\n")
                            log.write(f"Status: {info['release_status']}\n")
                            log.write(f"Platform: {info['platform']}\n")
                            log.write(f"Description: {info['description']}\n")
                            if info.get('image_url'):
                                log.write(f"Image URL: {info['image_url']}\n")
                            if info.get('thumbnail_url'):
                                log.write(f"Thumbnail URL: {info['thumbnail_url']}\n")
                            log.write("==================================================\n\n")
                    except UnicodeEncodeError:
                        # Fallback to ASCII with replacement characters for problematic chars
                        with open('api_log.txt', 'a', encoding='ascii', errors='replace') as log:
                            log.write("==================================================\n")
                            log.write(f"Avatar id:{info['id']}\n")
                            log.write(f"Avatar Name: {info['name']}\n")
                            log.write(f"Author: {info['author_name'].encode('ascii', 'replace').decode('ascii')}\n")
                            log.write(f"Status: {info['release_status']}\n")
                            log.write(f"Platform: {info['platform']}\n")
                            log.write(f"Description: {info['description'].encode('ascii', 'replace').decode('ascii')}\n")
                            if info.get('image_url'):
                                log.write(f"Image URL: {info['image_url']}\n")
                            if info.get('thumbnail_url'):
                                log.write(f"Thumbnail URL: {info['thumbnail_url']}\n")
                            log.write("==================================================\n\n")
                except KeyError as e:
                    print(f"Error: Missing field {e} in avatar info")
                    print("="*50)
        else:
            print(f"\n[!] {info}")
        
        # Wait 5 seconds before next avatar
        time.sleep(5)
    
    print("\nCompleted fetching all avatar information.")
    print("Thank you for using Avatar Information Fetcher!")

if __name__ == "__main__":
    main()
