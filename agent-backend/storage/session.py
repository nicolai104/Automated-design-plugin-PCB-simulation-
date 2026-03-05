from typing import Dict, Any, Optional
import json
import os
from datetime import datetime


class SessionStorage:
    def __init__(self, storage_dir: str = "./data/sessions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        try:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")

            session_data = {
                "session_id": session_id,
                "updated_at": datetime.now().isoformat(),
                "data": data
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")

            if not os.path.exists(file_path):
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        try:
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")

            if os.path.exists(file_path):
                os.remove(file_path)
                return True

            return False
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    def list_sessions(self) -> list:
        try:
            files = os.listdir(self.storage_dir)
            sessions = []

            for file in files:
                if file.endswith(".json"):
                    session_id = file.replace(".json", "")
                    session = self.get_session(session_id)
                    if session:
                        sessions.append({
                            "session_id": session_id,
                            "updated_at": session.get("updated_at")
                        })

            return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    def clear_old_sessions(self, days: int = 7) -> int:
        try:
            count = 0
            now = datetime.now()

            for session in self.list_sessions():
                session_id = session.get("session_id")
                updated_at = session.get("updated_at")

                if updated_at:
                    try:
                        session_time = datetime.fromisoformat(updated_at)
                        delta = (now - session_time).days

                        if delta > days:
                            if self.delete_session(session_id):
                                count += 1
                    except:
                        pass

            return count
        except Exception as e:
            print(f"Error clearing old sessions: {e}")
            return 0
