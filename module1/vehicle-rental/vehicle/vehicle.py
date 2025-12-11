from abc import ABC, abstractmethod

class Vehicle(ABC):
    def __init__(self, vehicle_id, brand, base_price):
        self.vehicle_id = vehicle_id
        self.brand = brand
        self.base_price = base_price
        self._is_rented = False

    @abstractmethod
    def display_details(self):
        pass

    @abstractmethod
    def calculate_rental_cost(self, days):
        pass

    @property
    def is_rented(self):
        return self._is_rented

    @is_rented.setter
    def is_rented(self, status):
        self._is_rented = status

    def rent(self):
        if self.is_rented:
            return False
        self.is_rented = True
        return True

    def return_vehicle(self):
        if not self.is_rented:
            return False
        self.is_rented = False
        return True

    def __str__(self):
        return f"{self.brand} {self.vehicle_id} with base price {self.base_price} {'rented' if self.is_rented else 'not rented'}"
