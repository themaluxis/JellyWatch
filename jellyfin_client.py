import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class JellyfinClient:
    """A client for interacting with the Jellyfin API."""

    def __init__(self):
        """Initializes the JellyfinClient."""
        self.server_url = os.getenv("JELLYFIN_SERVER_URL")
        self.api_key = os.getenv("JELLYFIN_API_KEY")
        self.user_id = os.getenv("JELLYFIN_USER_ID")

        if not self.server_url or not self.api_key:
            raise ValueError("JELLYFIN_SERVER_URL and JELLYFIN_API_KEY must be set.")

        self.headers = {
            "Authorization": f'MediaBrowser Token="{self.api_key}"',
            "Content-Type": "application/json",
        }

    def _get(self, endpoint, params=None):
        """
        Sends a GET request to the specified Jellyfin API endpoint.

        Args:
            endpoint (str): The API endpoint to request (e.g., "/Sessions").
            params (dict, optional): A dictionary of query parameters. Defaults to None.

        Returns:
            dict or None: The JSON response from the API, or None if the request fails.
        """
        try:
            response = requests.get(
                f"{self.server_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making GET request to {endpoint}: {e}")
            return None

    def get_sessions(self):
        """Gets all active sessions on the Jellyfin server."""
        return self._get("/Sessions")

    def get_latest_items(self):
        """Gets the latest added items for the configured user."""
        if not self.user_id:
            print("Warning: JELLYFIN_USER_ID is not set. Cannot fetch latest items.")
            return None
        return self._get(f"/Users/{self.user_id}/Items/Latest")

    def get_item(self, item_id):
        """Gets detailed information about a specific item."""
        return self._get(f"/Items/{item_id}")

    def get_user(self, user_id):
        """Gets detailed information about a specific user."""
        return self._get(f"/Users/{user_id}")

    def get_item_image_url(self, item_id, image_type="Primary"):
        """
        Gets the URL for an item's image.

        Args:
            item_id (str): The ID of the item.
            image_type (str): The type of image to get (e.g., "Primary", "Backdrop").

        Returns:
            str: The full URL to the image.
        """
        return f"{self.server_url}/Items/{item_id}/Images/{image_type}"
