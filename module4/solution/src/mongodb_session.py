"""
MongoDB Session Storage Module
Implements user session and shopping cart storage using MongoDB.
Handles unstructured session data for flexibility.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

load_dotenv()


class MongoDBSessions:
    """MongoDB manager for user sessions and shopping carts."""
    
    def __init__(self):
        """Initialize MongoDB Atlas connection."""
        try:
            # Get MongoDB Atlas URI from environment
            mongodb_uri = os.getenv('MONGODB_URI')
            
            if not mongodb_uri:
                raise ValueError(
                    "[ERROR] MONGODB_URI not found in environment variables!\n"
                    "[TIP] Please set MONGODB_URI in your .env file with your MongoDB Atlas connection string."
                )
            
            # Connect to MongoDB Atlas
            print("[INFO] Connecting to MongoDB Atlas...")
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database name from URI or use default
            db_name = os.getenv('DB_NAME', 'store')
            self.db = self.client[db_name]
            self.sessions = self.db['user_sessions']
            self.carts = self.db['shopping_carts']
            
            print(f"[SUCCESS] MongoDB Atlas connected to database: {db_name}")
        except ConnectionFailure as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            print("[TIP] Check your MONGODB_URI in the .env file")
            raise
        except ValueError as e:
            print(str(e))
            raise

    # SHOPPING CART OPERATIONS

    
    def create_or_update_cart(self, user_id: str, items: List[Dict]) -> bool:
        """
        Create or update shopping cart for a user.
        
        Args:
            user_id: User identifier
            items: List of cart items [{'product_id': int, 'quantity': int, 'name': str, 'price': float}]
        
        Returns:
            True if successful
        """
        try:
            cart_data = {
                'user_id': user_id,
                'items': items,
                'updated_at': datetime.utcnow(),
                'item_count': len(items),
                'total_items': sum(item.get('quantity', 0) for item in items)
            }
            
            # Upsert: update if exists, insert if not
            self.carts.update_one(
                {'user_id': user_id},
                {'$set': cart_data},
                upsert=True
            )
            
            print(f"[SUCCESS] Cart updated for user {user_id}: {len(items)} unique items")
            return True
        except Exception as e:
            print(f"[ERROR] Error updating cart: {e}")
            return False
    
    def get_cart(self, user_id: str) -> Optional[Dict]:
        """
        Retrieve shopping cart for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Cart dictionary or None
        """
        try:
            cart = self.carts.find_one({'user_id': user_id}, {'_id': 0})
            if cart:
                print(f"[SUCCESS] Retrieved cart for user {user_id}")
                return cart
            else:
                print(f"[WARNING] No cart found for user {user_id}")
                return None
        except Exception as e:
            print(f"[ERROR] Error retrieving cart: {e}")
            return None
    
    def add_to_cart(self, user_id: str, product_id: int, quantity: int, 
                    name: str, price: float) -> bool:
        """
        Add item to cart or update quantity if exists.
        
        Args:
            user_id: User identifier
            product_id: Product ID
            quantity: Quantity to add
            name: Product name
            price: Product price
        
        Returns:
            True if successful
        """
        try:
            # Get existing cart
            cart = self.get_cart(user_id)
            
            if cart:
                items = cart.get('items', [])
                # Check if product already in cart
                found = False
                for item in items:
                    if item['product_id'] == product_id:
                        item['quantity'] += quantity
                        found = True
                        break
                
                if not found:
                    items.append({
                        'product_id': product_id,
                        'name': name,
                        'price': price,
                        'quantity': quantity
                    })
            else:
                items = [{
                    'product_id': product_id,
                    'name': name,
                    'price': price,
                    'quantity': quantity
                }]
            
            return self.create_or_update_cart(user_id, items)
        except Exception as e:
            print(f"[ERROR] Error adding to cart: {e}")
            return False
    
    def remove_from_cart(self, user_id: str, product_id: int) -> bool:
        """
        Remove item from cart.
        
        Args:
            user_id: User identifier
            product_id: Product ID to remove
        
        Returns:
            True if successful
        """
        try:
            cart = self.get_cart(user_id)
            if cart:
                items = [item for item in cart.get('items', []) 
                        if item['product_id'] != product_id]
                return self.create_or_update_cart(user_id, items)
            return False
        except Exception as e:
            print(f"[ERROR] Error removing from cart: {e}")
            return False
    
    def clear_cart(self, user_id: str) -> bool:
        """
        Clear all items from cart.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful
        """
        try:
            self.carts.delete_one({'user_id': user_id})
            print(f"[SUCCESS] Cart cleared for user {user_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Error clearing cart: {e}")
            return False

    # SESSION OPERATIONS
    
    def create_session(self, user_id: str, session_data: Dict) -> bool:
        """
        Create or update user session with arbitrary data.
        
        Args:
            user_id: User identifier
            session_data: Dictionary with session information
        
        Returns:
            True if successful
        """
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
            
            print(f"[SUCCESS] Session created/updated for user {user_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Error creating session: {e}")
            return False
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        """
        Retrieve user session.
        
        Args:
            user_id: User identifier
        
        Returns:
            Session dictionary or None
        """
        try:
            session = self.sessions.find_one({'user_id': user_id}, {'_id': 0})
            if session:
                # Update last activity
                self.sessions.update_one(
                    {'user_id': user_id},
                    {'$set': {'last_activity': datetime.utcnow()}}
                )
                return session
            return None
        except Exception as e:
            print(f"[ERROR] Error retrieving session: {e}")
            return None
    
    def delete_session(self, user_id: str) -> bool:
        """
        Delete user session.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful
        """
        try:
            self.sessions.delete_one({'user_id': user_id})
            print(f"[SUCCESS] Session deleted for user {user_id}")
            return True
        except Exception as e:
            print(f"[ERROR] Error deleting session: {e}")
            return False

