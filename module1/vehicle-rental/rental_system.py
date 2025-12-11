class RentalSystem:
    def __init__(self):
        self.vehicles=[]
    
    def add_vehicle(self,vehicle):
        self.vehicles.append(vehicle)
    
    def show_available(self):
        print("Available Vehicles:")
        for vehicle in self.vehicles:
            if not vehicle.is_rented:
                print(vehicle)
    def display_rented_vehicles(self):
        print("Rented Vehicles:")
        for vehicle in self.vehicles:
            if vehicle.is_rented:
                print(vehicle)
                
    def show_all(self):
        print("All Vehicles:")
        for vehicle in self.vehicles:
            print(vehicle)
                
    def rent_vehicle(self,vehicle_id,days):
        for vehicle in self.vehicles:
            if vehicle.vehicle_id==vehicle_id:
                if vehicle.rent():
                    print(f"{vehicle_id}rented successful")
                else:
                    print(f"{vehicle_id}is already rented")
                return
        print(f"{vehicle_id}not found")
    
    def return_vehicle(self,vehicle_id):
        for vehicle in self.vehicles:
            if vehicle.vehicle_id==vehicle_id:
                if vehicle.return_vehicle():
                    print(f"{vehicle_id}returned successful")
                else:
                    print(f"{vehicle_id}is not rented")
                return
        print(f"{vehicle_id}not found")
        
    def calculate_cost(self, vehicle_id, days):
        for v in self.vehicles:
            if v.vehicle_id == vehicle_id:
                if not v.is_rented:
                    print(f"{vehicle_id} is not rented.")
                    return
                cost = v.calculate_rental_cost(days)
                print(f"Cost for {vehicle_id} for {days} days: ${cost}")
                return
        print(f"Vehicle {vehicle_id} not found.")
    
            
               
        