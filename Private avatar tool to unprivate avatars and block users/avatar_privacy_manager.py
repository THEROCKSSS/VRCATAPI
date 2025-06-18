import vrchatapi
from vrchatapi.api import avatars_api, authentication_api
from vrchatapi.models import UpdateAvatarRequest
from block_manager import login

class AvatarPrivacyManager:
    def __init__(self):
        # Use the existing login function from block_manager
        self.api_client, self.auth_api, _ = login()
        self.avatars_api = avatars_api.AvatarsApi(self.api_client)

    def get_my_avatars(self):
        """Get list of your owned avatars"""
        try:
            current_user = self.auth_api.get_current_user()            # Get avatars you own using search
            avatars = self.avatars_api.search_avatars(
                user_id=current_user.id,
                n=100,  # Get up to 100 avatars
                order="descending",
                release_status="all"  # Get both public and private avatars
            )
            return avatars
        except vrchatapi.ApiException as e:
            print(f"Exception when getting avatars: {e}")
            return None

    def get_avatar_details(self, avatar_id):
        """Get details about a specific avatar"""
        try:
            avatar = self.avatars_api.get_avatar(avatar_id)
            return avatar
        except vrchatapi.ApiException as e:
            print(f"Exception when getting avatar details: {e}")
            return None

    def set_avatar_privacy(self, avatar_id, is_private):
        """Set an avatar's privacy status
        Args:
            avatar_id (str): The ID of the avatar to update
            is_private (bool): True to make private, False to make public
        """
        try:
            # First get the current avatar details
            current_avatar = self.get_avatar_details(avatar_id)
            if not current_avatar:
                return None

            # Create update request with all required fields
            request = {
                "name": current_avatar.name,
                "description": current_avatar.description or "",
                "releaseStatus": "private" if is_private else "public",
                "version": current_avatar.version,
                "unityPackageUrl": current_avatar.unity_package_url,
                "unityVersion": "2019.4.31f1",  # Most commonly used Unity version for VRChat
                "assetVersion": current_avatar.version,  
                "assetUrl": current_avatar.unity_package_url,  # Same as unityPackageUrl
                "platform": "standalonewindows",  # PC platform
                "imageUrl": current_avatar.image_url
            }
            
            # Send update request 
            updated_avatar = self.avatars_api.update_avatar(
                avatar_id,
                update_avatar_request=request
            )
            
            return updated_avatar
        except vrchatapi.ApiException as e:
            print(f"Exception when updating avatar privacy: {e}")
            return None

def main():
    manager = AvatarPrivacyManager()
    
    while True:
        print("\nAvatar Privacy Manager")
        print("=====================")
        print("1. List all my avatars")
        print("2. Toggle avatar privacy (private/public)")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            # Get list of your avatars
            print("\nFetching your avatars...")
            avatars = manager.get_my_avatars()
            if avatars and len(avatars) > 0:
                print("\nYour avatars:")
                for i, avatar in enumerate(avatars, 1):
                    print(f"\n{i}. {avatar.name}")
                    print(f"   ID: {avatar.id}")
                    print(f"   Current status: {avatar.release_status}")
            else:
                print("\nNo avatars found or failed to fetch avatars")
                
        elif choice == "2":
            # Get list of your avatars
            print("\nFetching your avatars...")
            avatars = manager.get_my_avatars()
            if avatars and len(avatars) > 0:
                print("\nYour avatars:")
                for i, avatar in enumerate(avatars, 1):
                    status = "🔒 private" if avatar.release_status == "private" else "🌐 public"
                    print(f"{i}. {avatar.name} ({status})")
                
                try:
                    avatar_num = int(input("\nEnter the number of the avatar to modify: ")) - 1
                    if 0 <= avatar_num < len(avatars):
                        avatar = avatars[avatar_num]
                        current_private = avatar.release_status == "private"
                        make_private = not current_private  # Toggle the current status
                        
                        new_status = "private" if make_private else "public"
                        print(f"\nChanging '{avatar.name}' from {avatar.release_status} to {new_status}...")
                        
                        # Update privacy
                        updated = manager.set_avatar_privacy(avatar.id, make_private)
                        if updated:
                            print(f"Avatar privacy updated successfully!")
                            print(f"New status: {updated.release_status}")
                        else:
                            print("Failed to update avatar privacy")
                    else:
                        print("\nInvalid avatar number")
                except ValueError:
                    print("\nPlease enter a valid number")
            else:
                print("\nNo avatars found or failed to fetch avatars")
                
        elif choice == "3":
            print("\nGoodbye!")
            break
            
        else:
            print("\nInvalid choice. Please enter a number between 1-3.")

if __name__ == "__main__":
    main()
