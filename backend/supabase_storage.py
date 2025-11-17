"""
Supabase storage integration for Melo.
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SupabaseStorage:
    """Handle file storage using Supabase."""

    def __init__(self):
        self.enabled = False
        self.client: Optional[Client] = None

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if SUPABASE_AVAILABLE and supabase_url and supabase_key:
            try:
                self.client = create_client(supabase_url, supabase_key)
                self.enabled = True
                print("Supabase storage enabled")
            except Exception as e:
                print(f"Failed to initialize Supabase: {e}")
                self.enabled = False
        else:
            print("Supabase not configured - using local storage")

    def upload_file(
        self,
        bucket: str,
        file_path: Path,
        destination_path: str,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        Upload a file to Supabase Storage.

        Args:
            bucket: Bucket name (e.g., "melodies", "audio")
            file_path: Local file path to upload
            destination_path: Destination path in bucket
            content_type: MIME type of the file

        Returns:
            Public URL if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            # Upload to Supabase
            response = self.client.storage.from_(bucket).upload(
                destination_path,
                data,
                {"content-type": content_type}
            )

            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(destination_path)
            return public_url

        except Exception as e:
            print(f"Error uploading to Supabase: {e}")
            return None

    def get_public_url(self, bucket: str, file_path: str) -> Optional[str]:
        """
        Get public URL for a file in Supabase Storage.

        Args:
            bucket: Bucket name
            file_path: File path in bucket

        Returns:
            Public URL if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            return self.client.storage.from_(bucket).get_public_url(file_path)
        except Exception as e:
            print(f"Error getting public URL: {e}")
            return None

    def create_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Create a temporary signed URL for a file.

        Args:
            bucket: Bucket name
            file_path: File path in bucket
            expires_in: Expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL if successful, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            response = self.client.storage.from_(bucket).create_signed_url(
                file_path,
                expires_in
            )
            return response.get("signedURL")
        except Exception as e:
            print(f"Error creating signed URL: {e}")
            return None

    def save_melody_metadata(
        self,
        melody_id: str,
        metadata: dict
    ) -> bool:
        """
        Save melody metadata to Supabase database.

        Args:
            melody_id: Unique melody ID
            metadata: Metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            data = {
                "id": melody_id,
                "created_at": datetime.utcnow().isoformat(),
                **metadata
            }

            self.client.table("melodies").insert(data).execute()
            return True

        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False

    def get_melody_metadata(self, melody_id: str) -> Optional[dict]:
        """
        Retrieve melody metadata from Supabase database.

        Args:
            melody_id: Unique melody ID

        Returns:
            Metadata dictionary if found, None otherwise
        """
        if not self.enabled or not self.client:
            return None

        try:
            response = self.client.table("melodies").select("*").eq("id", melody_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            print(f"Error retrieving metadata: {e}")
            return None


# Global instance
supabase_storage = SupabaseStorage()
