from .vehicle import Vehicle

class Car(Vehicle):
    def __init__(self,vehicle_id,brand,base_price):
        super().__init__(vehicle_id,brand,base_price)
        
    def display_details(self):
        print("Car Details:")
        print(f"Vehicle ID: {self.vehicle_id}")
        print(f"Brand: {self.brand}")
        print(f"Base Price: {self.base_price}") 
        print(f"Is Rented: {'Yes' if self._is_rented else 'No'}") 
        
    def calculate_rental_cost(self,days):
        return self.base_price * days