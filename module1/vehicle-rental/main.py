from vehicle.car import Car
from vehicle.bike import Bike
from vehicle.truck import Truck
from rental_system import RentalSystem

def main():
    system = RentalSystem()

    

    while True:
        print("\n--- Vehicle Rental System ---")
        print("1. Show all vehicles")
        print("2. Show available vehicles")
        print("3. Rent vehicle")
        print("4. Return vehicle")
        print("5. Calculate cost")
        print("6. Add a new vehicle")  # <-- New option
        print("7. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            system.show_all()
        elif choice == "2":
            system.show_available()
        elif choice == "3":
            vid = input("Enter Vehicle ID to rent: ")
            days = int(input("Enter number of days: "))
            system.rent_vehicle(vid, days)
        elif choice == "4":
            vid = input("Enter Vehicle ID to return: ")
            system.return_vehicle(vid)
        elif choice == "5":
            vid = input("Enter Vehicle ID: ")
            days = int(input("Enter number of days: "))
            system.calculate_cost(vid, days)
        elif choice == "6":
            print("\nChoose vehicle type to add:")
            print("1. Car")
            print("2. Bike")
            print("3. Truck")
            vtype = input("Enter type: ")

            vid = input("Enter Vehicle ID: ")
            brand = input("Enter Brand: ")
            base_price = float(input("Enter Base Rate per day: "))

            if vtype == "1":
                
                vehicle = Car(vid, brand, base_price)
            elif vtype == "2":
                
                
                vehicle = Bike(vid, brand, base_price)
            elif vtype == "3":
                
                vehicle = Truck(vid, brand, base_price)
            else:
                print("Invalid vehicle type.")
                continue

            system.add_vehicle(vehicle)
            print(f"{vid} added successfully.")
        elif choice == "7":
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
