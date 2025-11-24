from datetime import datetime, timedelta

# -----------------------------
#        DATA STORAGE
# -----------------------------
clients = []
properties = []
rentals = []

# -----------------------------
#        DATA MODELS
# -----------------------------
class Client:
    def __init__(self, name, email=None, phone=None, address=None):
        self.id = len(clients) + 1
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address

class Property:
    RENT_PERIODS = ['monthly', 'yearly']

    def __init__(self, category, kind=None, address=None, floor_area=0, rent_amount=0, rent_period='monthly', description=''):
        self.id = len(properties) + 1
        self.category = category
        self.kind = kind
        self.address = address
        self.floor_area = floor_area
        self.rent_amount = rent_amount
        self.rent_period = rent_period
        self.description = description
        self.available = True

    def display_info(self):
        avail = 'Yes' if self.available else 'No'
        info = f"ID: {self.id} | Category: {self.category.title()} | Kind: {self.kind or 'N/A'} | " \
               f"Address: {self.address} | Floor Area: {self.floor_area} sqm | " \
               f"Rent: {self.rent_amount}/{self.rent_period} | Available: {avail}"
        return info

class Commercial(Property):
    def __init__(self, kind, address, floor_area, rent_amount, rent_period, description):
        super().__init__('commercial', kind, address, floor_area, rent_amount, rent_period, description)

class Residential(Property):
    def __init__(self, kind, address, floor_area, rent_amount, rent_period, description, bedrooms=0, bathrooms=0):
        super().__init__('residential', kind, address, floor_area, rent_amount, rent_period, description)
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms

class Land(Property):
    def __init__(self, address, floor_area, rent_amount, rent_period, description, land_use=None):
        super().__init__('land', None, address, floor_area, rent_amount, rent_period, description)
        self.land_use = land_use

class Resorts(Property):
    def __init__(self, kind, address, floor_area, rent_amount, rent_period, description, amenities=None):
        super().__init__('resorts', kind, address, floor_area, rent_amount, rent_period, description)
        self.amenities = amenities

class Venues(Property):
    def __init__(self, kind, address, floor_area, rent_amount, rent_period, description, capacity=0):
        super().__init__('venues', kind, address, floor_area, rent_amount, rent_period, description)
        self.capacity = capacity

class Rental:
    def __init__(self, client, property, start_date, end_date, total_amount, payment_frequency='monthly'):
        self.client = client
        self.property = property
        self.start_date = start_date
        self.end_date = end_date
        self.total_amount = total_amount
        self.payment_frequency = payment_frequency
        property.available = False
        self.next_due_date = self.calculate_next_due()

    def calculate_next_due(self):
        if self.payment_frequency == 'monthly':
            month = self.start_date.month + 1
            year = self.start_date.year
            if month > 12:
                month = 1
                year += 1
            day = min(self.start_date.day, 28)
            return datetime(year, month, day).date()
        else:  # yearly
            return datetime(self.start_date.year + 1, self.start_date.month, self.start_date.day).date()

# -----------------------------
#        INPUT HELPERS
# -----------------------------
def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Enter a number.")

def input_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Enter an integer.")

def input_yes_no(prompt):
    while True:
        ans = input(prompt).lower()
        if ans in ['yes', 'y']:
            return True
        elif ans in ['no', 'n']:
            return False
        print("Please answer yes or no.")

def input_date(prompt):
    while True:
        val = input(prompt)
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")

# -----------------------------
#        FEATURES
# -----------------------------
def add_property():
    print("\n=== Add New Property ===")
    print("Available categories: commercial, residential, land, resorts, venues")
    category = input("Enter category: ").strip().lower()
    if category not in ['commercial', 'residential', 'land', 'resorts', 'venues']:
        print("Invalid category!")
        return

    address = input("Enter address: ")
    floor_area = input_float("Enter floor area (sqm): ")
    yearly_rent = input_float("Enter yearly rent amount: ")
    monthly_rent = input_float("Enter monthly rent amount: ")
    print("Rent periods: monthly, yearly")
    rent_period = input("Enter rent period: ").strip().lower()
    rent_amount = yearly_rent if rent_period == 'yearly' else monthly_rent
    description = input("Enter description of property: ")

    if category == 'commercial':
        kind = input("Enter kind (e.g., office, warehouse, retail space, etc.): ")
        prop = Commercial(kind, address, floor_area, rent_amount, rent_period, description)
    elif category == 'residential':
        kind = input("Enter kind (e.g., house, condo, apartment): ")
        bedrooms = input_int("Enter number of bedrooms: ")
        bathrooms = input_int("Enter number of bathrooms: ")
        prop = Residential(kind, address, floor_area, rent_amount, rent_period, description, bedrooms, bathrooms)
    elif category == 'land':
        land_use = input("Enter land use (agricultural, residential, commercial): ")
        prop = Land(address, floor_area, rent_amount, rent_period, description, land_use)
    elif category == 'resorts':
        kind = input("Enter kind (e.g., beach resort, mountain resort): ")
        amenities = input("Enter amenities (pool, spa, gym, etc.): ")
        prop = Resorts(kind, address, floor_area, rent_amount, rent_period, description, amenities)
    elif category == 'venues':
        kind = input("Enter kind (e.g., wedding venue, conference hall): ")
        capacity = input_int("Enter capacity: ")
        prop = Venues(kind, address, floor_area, rent_amount, rent_period, description, capacity)

    properties.append(prop)
    print(f"{category.title()} property added successfully!")

def view_properties():
    if not properties:
        print("No properties available.")
        return
    print("\n--- Properties ---")
    for p in properties:
        print(p.display_info())
    print("------------------")

def view_clients():
    if not clients:
        print("No clients found.")
        return
    print("\n=== Clients with Rentals ===")
    for c in clients:
        print(f"Client: {c.name} | Email: {c.email or 'N/A'} | Address: {c.address or 'N/A'} | Phone: {c.phone or 'N/A'}")
        client_rentals = [r for r in rentals if r.client == c]
        for r in client_rentals:
            print(f"  - Rented: {r.property.kind or 'Land'} in {r.property.address} | Next Due: {r.next_due_date}")
    print("------------------")

def rent_property():
    if not properties:
        print("No properties available.")
        return
    available_props = [p for p in properties if p.available]
    if not available_props:
        print("No available properties to rent.")
        return
    print("\nAvailable Properties:")
    for i, p in enumerate(available_props, 1):
        print(f"{i}. {p.display_info()}")
    choice = input_int("Select property number: ") - 1
    if choice < 0 or choice >= len(available_props):
        print("Invalid choice!")
        return
    prop = available_props[choice]

    name = input("Enter client name: ")
    email = input("Enter client email: ")
    phone = input("Enter client phone: ")
    address = input("Enter client address: ")
    client = Client(name, email, phone, address)
    clients.append(client)

    start_date = input_date("Enter start date (YYYY-MM-DD): ")
    end_date = input_date("Enter end date (YYYY-MM-DD): ")
    if end_date <= start_date:
        print("End date must be after start date.")
        return

    duration_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    total_amount = prop.rent_amount * duration_months if prop.rent_period=='monthly' else (prop.rent_amount/12)*duration_months

    payment_frequency = input("Enter payment frequency (monthly/yearly): ").strip().lower()
    rental = Rental(client, prop, start_date, end_date, total_amount, payment_frequency)
    rentals.append(rental)
    print(f"Property rented successfully to {client.name}. Total amount: {total_amount:.2f}")

def view_rentals():
    if not rentals:
        print("No active rentals.")
        return
    print("\n=== Currently Rented Properties ===")
    for r in rentals:
        if not r.property.available:
            remaining_days = (r.end_date - datetime.today().date()).days
            print(f"Property: {r.property.kind or 'Land'} in {r.property.address} | Rented by: {r.client.name} | Remaining Days: {remaining_days}")
    print("------------------")

def view_due_payments():
    today = datetime.today().date()
    upcoming = today + timedelta(days=30)
    due_rentals = [r for r in rentals if today <= r.next_due_date <= upcoming]
    if not due_rentals:
        print("No payments due in the next month.")
        return
    print("\n=== Payments Due in 1 Month ===")
    for r in due_rentals:
        print(f"Client: {r.client.name} | Property: {r.property.kind or 'Land'} in {r.property.address} | Next Due: {r.next_due_date} | Amount: {r.total_amount:.2f}")
    print("------------------")

# -----------------------------
#        MAIN MENU
# -----------------------------
def main_menu():
    while True:
        print("\n=== Property Leasing System ===")
        print("1) Clients - View all clients with rentals")
        print("2) Properties - View by category & Add property")
        print("3) Rent - Rent a property")
        print("4) Rentals - View currently rented properties")
        print("5) Due Payments - View payments due in 1 month")
        print("6) Exit")
        choice = input("Choose option: ").strip()
        if choice == '1':
            view_clients()
        elif choice == '2':
            while True:
                print("\n--- Properties Menu ---")
                print("1) View Properties")
                print("2) Add Property")
                print("3) Back to Main Menu")
                sub_choice = input("Choose option: ").strip()
                if sub_choice == '1':
                    view_properties()
                elif sub_choice == '2':
                    add_property()
                elif sub_choice == '3':
                    break
                else:
                    print("Invalid option.")
        elif choice == '3':
            rent_property()
        elif choice == '4':
            view_rentals()
        elif choice == '5':
            view_due_payments()
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid option.")

# -----------------------------
#        RUN
# -----------------------------
if __name__ == "__main__":
    main_menu()
