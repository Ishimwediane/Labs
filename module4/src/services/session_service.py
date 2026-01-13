from typing import Dict, Optional
from datetime import datetime
from src.database.mongo_client import mongodb
from src.utils.logger import log_success, log_error


class SessionService:
    def __init__(self):
        self.sessions = mongodb.get_collection('user_sessions')
    
    def create_session(self, user_id: str, session_data: Dict) -> bool:
        try:
            session = {
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'data': session_data
            }
            
            self.sessions.update_one(
                {'user_id': user_id},
                {'$set': session},
                upsert=True
            )
            
            log_success(f"Session created/updated for user {user_id}")
            return True
        except Exception as e:
            log_error(f"Error creating session: {e}")
            return False
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        try:
            session = self.sessions.find_one({'user_id': user_id}, {'_id': 0})
            
            if session:
                self.sessions.update_one(
                    {'user_id': user_id},
                    {'$set': {'last_activity': datetime.utcnow()}}
                )
                log_success(f"Retrieved session for user {user_id}")
                return session
            
            return None
        except Exception as e:
            log_error(f"Error retrieving session: {e}")
            return None
    
    def delete_session(self, user_id: str) -> bool:
        try:
            self.sessions.delete_one({'user_id': user_id})
            log_success(f"Session deleted for user {user_id}")
            return True
        except Exception as e:
            log_error(f"Error deleting session: {e}")
            return False
    
    def update_last_activity(self, user_id: str) -> bool:
        try:
            result = self.sessions.update_one(
                {'user_id': user_id},
                {'$set': {'last_activity': datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                log_success(f"Updated last activity for user {user_id}")
                return True
            
            return False
        except Exception as e:
            log_error(f"Error updating last activity: {e}")
            return False

session_service = SessionService()
