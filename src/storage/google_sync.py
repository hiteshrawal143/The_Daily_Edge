"""Free Google Workspace sync backends (Apps Script Bridge or Free OAuth Desktop).

Zero paid APIs, zero billing accounts, zero hardcoded credentials.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from src.config import ROOT_DIR, SHEET_SCHEMAS, load_settings
from src.storage.local_db import LocalKnowledgeDB

OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]


class GoogleWorkspaceSync:
    """Syncs local SQLite records and briefs to Google Sheets, Docs, Drive, and Gmail."""

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.settings = settings or load_settings()
        self.mode = self.settings.get("google_sync_mode", "local_only")

    def is_configured(self) -> bool:
        """Return True if a Google sync mode is configured and ready."""
        if self.mode == "apps_script_bridge":
            return bool(self.settings.get("apps_script_webapp_url"))
        if self.mode == "google_oauth":
            cred_path = self._resolve_path(self.settings.get("google_credentials_path", "credentials.json"))
            return cred_path.exists()
        return False

    def _resolve_path(self, raw_path: str) -> Path:
        p = Path(raw_path)
        return p if p.is_absolute() else ROOT_DIR / p

    def sync_all(self, db: LocalKnowledgeDB, send_email: bool = False) -> dict[str, Any]:
        """Push local database tabs to Google Sheets using the configured free backend."""
        if self.mode == "apps_script_bridge":
            return self._sync_via_apps_script(db, send_email=send_email)
        if self.mode == "google_oauth":
            return self._sync_via_oauth(db)
        return {
            "status": "skipped_local_only",
            "message": "GOOGLE_SYNC_MODE=local_only. Local SQLite database is up to date.",
        }

    def _sync_via_apps_script(self, db: LocalKnowledgeDB, send_email: bool = False) -> dict[str, Any]:
        """Send structured JSON payload to the user's free Google Apps Script Web App."""
        url = self.settings.get("apps_script_webapp_url", "")
        secret = self.settings.get("apps_script_shared_secret", "")
        if not url:
            return {"status": "not_configured", "message": "APPS_SCRIPT_WEBAPP_URL is blank in .env"}

        # Respect strict email safety gate
        allow_send = bool(send_email and self.settings.get("allow_email_send") and self.settings.get("recipient_email"))

        payload = {
            "secret": secret,
            "action": "sync_payload",
            "send_email": allow_send,
            "recipient_email": self.settings.get("recipient_email", "") if allow_send else "",
            "tabs": {tab: db.get_tab_rows(tab, limit=100) for tab in SHEET_SCHEMAS},
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return {"status": "ok", "backend": "apps_script_bridge", "response": resp.json()}
        except (requests.RequestException, ValueError) as exc:
            return {"status": "error", "backend": "apps_script_bridge", "message": str(exc)}

    def _get_oauth_credentials(self):
        """Authenticate via free Google OAuth Desktop flow (no billing required)."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        cred_path = self._resolve_path(self.settings.get("google_credentials_path", "credentials.json"))
        token_path = self._resolve_path(self.settings.get("google_token_path", "token.json"))

        if not cred_path.exists():
            raise FileNotFoundError(
                f"OAuth credentials file not found at {cred_path}. See NEXT_STEPS.md to create a free Desktop OAuth ID or use Apps Script."
            )

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), OAUTH_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), OAUTH_SCOPES)
                creds = flow.run_local_server(port=0)
            with token_path.open("w", encoding="utf-8") as fh:
                fh.write(creds.to_json())
        return creds

    def _sync_via_oauth(self, db: LocalKnowledgeDB) -> dict[str, Any]:
        """Create/update 'LifeTimeLibrary Knowledge Database' spreadsheet via gspread."""
        import gspread

        try:
            creds = self._get_oauth_credentials()
            gc = gspread.authorize(creds)
            sheet_name = self.settings.get("google_spreadsheet_name", "LifeTimeLibrary Knowledge Database")

            try:
                spreadsheet = gc.open(sheet_name)
            except gspread.SpreadsheetNotFound:
                spreadsheet = gc.create(sheet_name)

            existing_titles = {ws.title: ws for ws in spreadsheet.worksheets()}
            synced_tabs: list[str] = []

            for tab_name, headers in SHEET_SCHEMAS.items():
                if tab_name not in existing_titles:
                    ws = spreadsheet.add_worksheet(title=tab_name, rows=500, cols=len(headers))
                else:
                    ws = existing_titles[tab_name]

                rows = list(reversed(db.get_tab_rows(tab_name, limit=500)))
                matrix = [headers] + [[str(r.get(col, "")) for col in headers] for r in rows]
                ws.clear()
                ws.update("A1", matrix)
                synced_tabs.append(tab_name)

            return {
                "status": "ok",
                "backend": "google_oauth",
                "spreadsheet_url": spreadsheet.url,
                "tabs_synced": synced_tabs,
            }
        except Exception as exc:  # pragma: no cover - requires live OAuth credentials
            return {"status": "error", "backend": "google_oauth", "message": str(exc)}

    def create_google_doc_and_pdf(self, title: str, markdown_body: str, folder_subpath: str = "Daily Reports") -> dict[str, str]:
        """Create a Google Doc and export a PDF copy in Google Drive using free OAuth or Apps Script."""
        if self.mode == "apps_script_bridge":
            url = self.settings.get("apps_script_webapp_url", "")
            secret = self.settings.get("apps_script_shared_secret", "")
            if not url:
                return {"doc_url": "", "pdf_url": "", "status": "not_configured"}
            try:
                resp = requests.post(
                    url,
                    json={
                        "secret": secret,
                        "action": "create_doc_and_pdf",
                        "title": title,
                        "body": markdown_body,
                        "folder": folder_subpath,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as exc:
                return {"doc_url": "", "pdf_url": "", "status": f"error: {exc}"}

        if self.mode == "google_oauth":
            try:
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaIoBaseDownload
                import io

                creds = self._get_oauth_credentials()
                drive_svc = build("drive", "v3", credentials=creds)
                docs_svc = build("docs", "v1", credentials=creds)

                root_id = self._ensure_drive_folder(drive_svc, self.settings.get("google_drive_root_folder", "LifeTimeLibrary"))
                target_folder_id = self._ensure_drive_folder(drive_svc, folder_subpath, parent_id=root_id)
                pdf_folder_id = self._ensure_drive_folder(drive_svc, "PDF Reports", parent_id=root_id)

                doc = docs_svc.documents().create(body={"title": title}).execute()
                doc_id = doc["documentId"]
                docs_svc.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": [{"insertText": {"location": {"index": 1}, "text": markdown_body}}]},
                ).execute()

                drive_svc.files().update(fileId=doc_id, addParents=target_folder_id, fields="id, parents").execute()

                # Export PDF via free Drive export endpoint
                request = drive_svc.files().export_media(fileId=doc_id, mimeType="application/pdf")
                buf = io.BytesIO()
                downloader = MediaIoBaseDownload(buf, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

                from googleapiclient.http import MediaIoBaseUpload

                buf.seek(0)
                pdf_meta = {"name": f"{title}.pdf", "parents": [pdf_folder_id]}
                media = MediaIoBaseUpload(buf, mimetype="application/pdf")
                pdf_file = drive_svc.files().create(body=pdf_meta, media_body=media, fields="id, webViewLink").execute()

                return {
                    "status": "ok",
                    "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
                    "pdf_url": pdf_file.get("webViewLink", ""),
                }
            except Exception as exc:  # pragma: no cover
                return {"doc_url": "", "pdf_url": "", "status": f"error: {exc}"}

        return {"doc_url": "", "pdf_url": "", "status": "local_only"}

    @staticmethod
    def _ensure_drive_folder(drive_svc, name: str, parent_id: str | None = None) -> str:
        """Find or create a Google Drive folder by name."""
        q = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        res = drive_svc.files().list(q=q, fields="files(id, name)").execute()
        files = res.get("files", [])
        if files:
            return files[0]["id"]
        meta: dict[str, Any] = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            meta["parents"] = [parent_id]
        created = drive_svc.files().create(body=meta, fields="id").execute()
        return created["id"]
