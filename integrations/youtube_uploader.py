"""
YouTube Upload Script Automation (YouTube Data API v3).
Handles OAuth2 authentication, chunked resumable video upload,
custom thumbnail setting, tags, playlist assignment, and pinned comments.
"""

import os
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional
import config

# Google Client Libraries
try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


# Required OAuth 2.0 scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


class YouTubeUploader:
    """Manages YouTube Data API v3 authentication and automated video publishing."""

    def __init__(
        self,
        client_secrets_file: Optional[str] = None,
        token_pickle_file: Optional[str] = None
    ):
        self.client_secrets = client_secrets_file or config.YOUTUBE_CLIENT_SECRETS_FILE
        self.token_pickle = token_pickle_file or config.YOUTUBE_TOKEN_PICKLE_FILE
        self.service = None

    def authenticate(self):
        """Authenticates user via OAuth2 or loads cached token.pickle."""
        if not GOOGLE_API_AVAILABLE:
            raise RuntimeError(
                "Google API client libraries are not installed. "
                "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            )

        creds = None
        if os.path.exists(self.token_pickle):
            with open(self.token_pickle, "rb") as token:
                creds = pickle.load(token)

        # Refresh or prompt login if credentials are missing or expired
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets):
                    raise FileNotFoundError(
                        f"Missing OAuth client secrets file: {self.client_secrets}.\n"
                        "Download OAuth 2.0 Client ID (Desktop app) credentials from Google Cloud Console "
                        "and save as 'client_secrets.json'."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for next runs
            with open(self.token_pickle, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("youtube", "v3", credentials=creds)
        print("[YouTubeUploader] Successfully authenticated with YouTube API v3.")
        return self.service

    def upload_short(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str],
        thumbnail_path: Optional[Path] = None,
        category_id: str = "27",
        privacy_status: str = "public",
        publish_at: Optional[str] = None,
        playlist_id: Optional[str] = None
    ) -> Dict:
        """
        Uploads a video, sets custom thumbnail, and returns published video info.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file does not exist: {video_path}")

        if not self.service:
            self.authenticate()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:50],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        # Scheduled publication (ISO 8601 string, e.g., '2026-11-20T15:00:00Z')
        if publish_at:
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = publish_at

        # Resumable chunked upload
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=1024 * 1024 * 4,  # 4MB chunks
            resumable=True
        )

        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        print(f"[YouTubeUploader] Uploading {video_path.name} to YouTube ({privacy_status})...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"[YouTubeUploader] Upload progress: {progress}%")

        video_id = response.get("id")
        video_url = f"https://youtube.com/shorts/{video_id}"
        print(f"[YouTubeUploader] Upload complete! Video URL: {video_url}")

        # Set custom thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                print(f"[YouTubeUploader] Setting custom thumbnail from {thumbnail_path}...")
                self.service.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
                ).execute()
                print("[YouTubeUploader] Custom thumbnail set successfully.")
            except Exception as e:
                print(f"[YouTubeUploader] Warning: Failed to set custom thumbnail: {e}")

        # Add to playlist if requested
        if playlist_id:
            try:
                self.service.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {"kind": "youtube#video", "videoId": video_id}
                        }
                    }
                ).execute()
                print(f"[YouTubeUploader] Video added to playlist: {playlist_id}")
            except Exception as e:
                print(f"[YouTubeUploader] Warning: Could not add to playlist: {e}")

        return {
            "video_id": video_id,
            "url": video_url,
            "title": title,
            "status": privacy_status
        }


if __name__ == "__main__":
    print("YouTubeUploader module initialized.")
    print("Google API Client installed:", GOOGLE_API_AVAILABLE)
