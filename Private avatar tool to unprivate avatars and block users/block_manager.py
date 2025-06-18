import vrchatapi
from vrchatapi.api import authentication_api, users_api
from vrchatapi.exceptions import ApiException, UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode
import json
import os
import time
from http.cookiejar import Cookie
import sys
import time

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
            api_client.user_agent = "VRChatBlockManager/1.0.0"
            
            # Try loading cookies first
            if load_cookies(api_client):
                print("\n[✓] Loaded saved cookies - attempting session reuse")
            
            auth_api = authentication_api.AuthenticationApi(api_client)
            users_api_instance = users_api.UsersApi(api_client)

            try:
                current_user = auth_api.get_current_user()
                print(f"\nLogged in as: {current_user.display_name}")
                save_cookies(api_client)
                return api_client, auth_api, users_api_instance

            except UnauthorizedException as e:
                if "2 Factor Authentication" in str(e) or "Email 2 Factor Authentication" in str(e):
                    code = input("2FA Code: ")
                    if "Email" in str(e):
                        auth_api.verify2_fa_email_code(two_factor_email_code=TwoFactorEmailCode(code))
                    else:
                        auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(code))
                    current_user = auth_api.get_current_user()
                    print(f"\nLogged in as: {current_user.display_name}")
                    save_cookies(api_client)
                    return api_client, auth_api, users_api_instance
                else:
                    print(f"\nError: {str(e)}")

        except ApiException as e:
            print(f"\nError during login: {str(e)}")
            
        retry = input("\nWould you like to try again? (y/n): ")
        if retry.lower() != 'y':
            sys.exit(1)

def read_user_ids():
    """Read user IDs from the file"""
    try:
        with open('usrids.txt', 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("\n[!] usrids.txt not found. Creating new file.")
        with open('usrids.txt', 'w') as f:
            pass
        return []

def add_user_id(user_id):
    """Add a user ID to the file if not already present"""
    user_ids = read_user_ids()
    if user_id not in user_ids:
        with open('usrids.txt', 'a') as f:
            f.write(f"{user_id}\n")

def main():
    api_client, auth_api, users_api = login()
    moderation_api = vrchatapi.api.playermoderation_api.PlayermoderationApi(api_client)

    while True:
        print("\nVRChat User Block Manager")
        print("=======================")
        print("1. Block User by ID")
        print("2. Unblock User by ID")
        print("3. List Blocked Users")
        print("4. Block All Users from File")
        print("5. Unblock All Users from File")
        print("6. List Users in File")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == "1":
            user_id = input("Enter the UserID to block: ")
            try:
                moderation_request = {"moderated": user_id, "type": "block"}
                moderation_api.moderate_user(moderation_request)
                print(f"\n[✓] Successfully blocked user: {user_id}")
                add_user_id(user_id)
                print("[✓] Added user ID to file")
            except ApiException as e:
                print(f"\n[!] Error blocking user: {str(e)}")

        elif choice == "2":
            user_id = input("Enter the UserID to unblock: ")
            try:
                moderation_request = {"moderated": user_id, "type": "block"}
                moderation_api.unmoderate_user(moderation_request)
                print(f"\n[✓] Successfully unblocked user: {user_id}")
            except ApiException as e:
                print(f"\n[!] Error unblocking user: {str(e)}")

        elif choice == "3":
            try:
                moderations = moderation_api.get_player_moderations(type="block")
                if moderations:
                    print("\nBlocked Users:")
                    print("==============")
                    for mod in moderations:
                        print(f"{mod.target_display_name} ({mod.target_user_id})")
                else:
                    print("\nNo users are currently blocked.")
            except ApiException as e:
                print(f"\n[!] Error fetching blocked users: {str(e)}")

        elif choice == "4":
            user_ids = read_user_ids()
            if not user_ids:
                print("\n[!] No user IDs found in file")
                continue
                
            print(f"\nFound {len(user_ids)} users to block")
            print("Processing with 1 second delay between users...")
            
            for user_id in user_ids:
                try:
                    moderation_request = {"moderated": user_id, "type": "block"}
                    moderation_api.moderate_user(moderation_request)
                    print(f"[✓] Blocked {user_id}")
                    time.sleep(1)  # 1 second delay
                except ApiException as e:
                    print(f"[!] Error blocking {user_id}: {str(e)}")

        elif choice == "5":
            user_ids = read_user_ids()
            if not user_ids:
                print("\n[!] No user IDs found in file")
                continue
                
            print(f"\nFound {len(user_ids)} users to unblock")
            print("Processing with 1 second delay between users...")
            
            for user_id in user_ids:
                try:
                    moderation_request = {"moderated": user_id, "type": "block"}
                    moderation_api.unmoderate_user(moderation_request)
                    print(f"[✓] Unblocked {user_id}")
                    time.sleep(1)  # 1 second delay
                except ApiException as e:
                    print(f"[!] Error unblocking {user_id}: {str(e)}")

        elif choice == "6":
            user_ids = read_user_ids()
            if user_ids:
                print("\nUsers in File:")
                print("=============")
                for user_id in user_ids:
                    print(user_id)
            else:
                print("\nNo users found in file")

        elif choice == "7":
            print("\nGoodbye!")
            break

        else:
            print("\n[!] Invalid choice. Please enter a number between 1-7.")

if __name__ == "__main__":
    main()
