from typing import List, Dict, Optional
from datetime import datetime
from src.database.mongo_client import mongodb
from src.utils.logger import log_success, log_error, log_warning


class CartService:
    def __init__(self):
        """cart with MongoDB """
        self.carts = mongodb.get_collection('shopping_carts')
    
    def add_to_cart(self, user_id: str, product_id: int, quantity: int,
                   name: str, price: float) -> bool:
        try:
            cart = self.get_cart(user_id)            
            if cart:
                items = cart.get('items', [])
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
            
            return self._update_cart(user_id, items)
        except Exception as e:
            log_error(f"Error adding to cart: {e}")
            return False
    
    def remove_from_cart(self, user_id: str, product_id: int) -> bool:
        try:
            cart = self.get_cart(user_id)
            
            if cart:
                items = [item for item in cart.get('items', [])
                        if item['product_id'] != product_id]
                return self._update_cart(user_id, items)
            
            return False
        except Exception as e:
            log_error(f"Error removing from cart: {e}")
            return False
    
    def get_cart(self, user_id: str) -> Optional[Dict]:
        try:
            cart = self.carts.find_one({'user_id': user_id}, {'_id': 0})
            
            if cart:
                log_success(f"Retrieved cart for user {user_id}")
                return cart
            else:
                log_warning(f"No cart found for user {user_id}")
                return None
        except Exception as e:
            log_error(f"Error retrieving cart: {e}")
            return None
    
    def clear_cart(self, user_id: str) -> bool:
        try:
            self.carts.delete_one({'user_id': user_id})
            log_success(f"Cart cleared for user {user_id}")
            return True
        except Exception as e:
            log_error(f"Error clearing cart: {e}")
            return False
    
    def _update_cart(self, user_id: str, items: List[Dict]) -> bool:
        try:
            cart_data = {
                'user_id': user_id,
                'items': items,
                'updated_at': datetime.utcnow(),
                'item_count': len(items),
                'total_items': sum(item.get('quantity', 0) for item in items)
            }
            
            self.carts.update_one(
                {'user_id': user_id},
                {'$set': cart_data},
                upsert=True
            )
            
            log_success(f"Cart updated for user {user_id}: {len(items)} unique items")
            return True
        except Exception as e:
            log_error(f"Error updating cart: {e}")
            return False

cart_service = CartService()
