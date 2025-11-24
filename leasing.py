"""
Property Leasing App with SQLite (Single User Version)
"""

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import shutil

DB_FILE = "leasing.db"
DATE_FMT = "%Y-%m-%d"
PICTURES_DIR = "property_pictures"


class Database:
    
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._create_pictures_dir()

    def _create_pictures_dir(self):
        """Create directory for storing property pictures"""
        if not os.path.exists(PICTURES_DIR):
            os.makedirs(PICTURES_DIR)

    def _create_tables(self):
        c = self.conn.cursor()
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                kind TEXT,
                address TEXT,
                floor_area REAL,
                rent_amount REAL,
                rent_period TEXT NOT NULL,
                picture_path TEXT,
                description TEXT,
                is_available INTEGER DEFAULT 1,
                bedrooms INTEGER,
                bathrooms INTEGER,
                land_use TEXT,
                amenities TEXT,
                capacity INTEGER
            );

            CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                duration_months INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                payment_frequency TEXT NOT NULL,
                next_due_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(property_id) REFERENCES properties(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                property_id INTEGER,
                amount REAL NOT NULL,
                paid_on TEXT NOT NULL,
                frequency TEXT NOT NULL,
                next_due TEXT,
                notes TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(property_id) REFERENCES properties(id)
            );
            """
        )
        self.conn.commit()

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def query(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def close(self):
        self.conn.close()


class PictureManager:
    """Manages property picture uploads and storage"""
    
    @staticmethod
    def upload_picture(property_id: int, source_path: str) -> str:
        """Upload a picture for a property"""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Get file extension
        _, extension = os.path.splitext(source_path)
        
        # Create new filename with property ID
        new_filename = f"property_{property_id}{extension}"
        destination_path = os.path.join(PICTURES_DIR, new_filename)
        
        # Copy file to pictures directory
        shutil.copy2(source_path, destination_path)
        
        return destination_path
    
    @staticmethod
    def get_picture_path(property_id: int) -> Optional[str]:
        """Get the picture path for a property"""
        # Look for any file that starts with property_{id}
        pattern = f"property_{property_id}."
        for filename in os.listdir(PICTURES_DIR):
            if filename.startswith(pattern):
                return os.path.join(PICTURES_DIR, filename)
        return None
    
    @staticmethod
    def delete_picture(property_id: int):
        """Delete picture for a property"""
        picture_path = PictureManager.get_picture_path(property_id)
        if picture_path and os.path.exists(picture_path):
            os.remove(picture_path)
    
    @staticmethod
    def list_supported_formats():
        """List supported picture formats"""
        return ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']


class Person(ABC):
    def __init__(self, name, email=None, phone=None):
        self._name = name
        self._email = email
        self._phone = phone

    @abstractmethod
    def save(self, db: Database):
        pass

    def contact_info(self):
        return f"{self._name} | Email: {self._email or 'N/A'} | Phone: {self._phone or 'N/A'}"


class Client(Person):
    def __init__(self, name, email=None, phone=None, address=None, notes=None, client_id=None):
        super().__init__(name, email, phone)
        self.address = address
        self.notes = notes
        self.id = client_id

    def save(self, db: Database):
        if self.id:
            db.execute(
                "UPDATE clients SET name=?, email=?, phone=?, address=?, notes=? WHERE id=?",
                (self._name, self._email, self._phone, self.address, self.notes, self.id),
            )
        else:
            cur = db.execute(
                "INSERT INTO clients (name, email, phone, address, notes) VALUES (?, ?, ?, ?, ?)",
                (self._name, self._email, self._phone, self.address, self.notes),
            )
            self.id = cur.lastrowid
        return self.id


class Property(ABC):
    """Abstract base class for all properties"""
    
    RENT_PERIODS = ['monthly', 'yearly']
    
    def __init__(self, category, kind, address=None, floor_area=0.0, rent_amount=0.0,
                 rent_period="monthly", picture_path=None, description="", is_available=True, prop_id=None):
        self._category = category
        self._kind = kind
        self._address = address
        self._floor_area = float(floor_area)
        self._rent_amount = float(rent_amount)
        self._rent_period = rent_period
        self._picture_path = picture_path
        self._description = description
        self._is_available = is_available
        self.id = prop_id

    @abstractmethod
    def get_specific_details(self) -> Dict:
        """Return category-specific details"""
        pass

    def save(self, db: Database):
        """Save property to database - common fields"""
        specific_details = self.get_specific_details()
        
        avail = 1 if self._is_available else 0
        if self.id:
            db.execute(
                """UPDATE properties SET category=?, kind=?, address=?, floor_area=?, rent_amount=?, 
                rent_period=?, picture_path=?, description=?, is_available=?, bedrooms=?, 
                bathrooms=?, land_use=?, amenities=?, capacity=? WHERE id=?""",
                (self._category, self._kind, self._address, self._floor_area, self._rent_amount, 
                 self._rent_period, self._picture_path, self._description, avail,
                 specific_details.get('bedrooms'), specific_details.get('bathrooms'), 
                 specific_details.get('land_use'), specific_details.get('amenities'), 
                 specific_details.get('capacity'), self.id),
            )
        else:
            cur = db.execute(
                """INSERT INTO properties (category, kind, address, floor_area, rent_amount, 
                rent_period, picture_path, description, is_available, bedrooms, bathrooms, 
                land_use, amenities, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self._category, self._kind, self._address, self._floor_area, self._rent_amount, 
                 self._rent_period, self._picture_path, self._description, avail,
                 specific_details.get('bedrooms'), specific_details.get('bathrooms'),
                 specific_details.get('land_use'), specific_details.get('amenities'), 
                 specific_details.get('capacity')),
            )
            self.id = cur.lastrowid
        return self.id

    def display_info(self):
        base_info = f"ID: {self.id} | Category: {self._category.title()} | Kind: {self._kind or 'N/A'} | " \
                   f"Address: {self._address} | Floor Area: {self._floor_area} sqm | " \
                   f"Rent: ₱{self._rent_amount}/{self._rent_period} | " \
                   f"Available: {'Yes' if self._is_available else 'No'}"
        
        specific_info = self._get_specific_display_info()
        if specific_info:
            base_info += f" | {specific_info}"
        
        return base_info

    def _get_specific_display_info(self) -> str:
        """Get category-specific display information"""
        details = self.get_specific_details()
        if self._category == 'commercial':
            return "Commercial Property"
        elif self._category == 'residential':
            return f"Bedrooms: {details.get('bedrooms', 0)} | Bathrooms: {details.get('bathrooms', 0)}"
        elif self._category == 'land':
            return f"Land Use: {details.get('land_use', 'N/A')}"
        elif self._category == 'resorts':
            return f"Amenities: {details.get('amenities', 'N/A')}"
        elif self._category == 'venues':
            return f"Capacity: {details.get('capacity', 0)}"
        return ""

    def upload_picture(self, source_path: str):
        """Upload picture for this property"""
        if self.id:
            try:
                new_path = PictureManager.upload_picture(self.id, source_path)
                self._picture_path = new_path
                return True
            except Exception as e:
                print(f"Error uploading picture: {e}")
                return False
        return False

    def get_picture_info(self):
        """Get picture information"""
        if self._picture_path and os.path.exists(self._picture_path):
            return f"Picture: {os.path.basename(self._picture_path)}"
        elif PictureManager.get_picture_path(self.id):
            picture_path = PictureManager.get_picture_path(self.id)
            self._picture_path = picture_path
            return f"Picture: {os.path.basename(picture_path)}"
        else:
            return "No picture available"


class CommercialProperty(Property):
    def __init__(self, kind, address=None, floor_area=0.0, rent_amount=0.0,
                 rent_period="monthly", picture_path=None, description="", is_available=True, prop_id=None):
        super().__init__('commercial', kind, address, floor_area, rent_amount,
                        rent_period, picture_path, description, is_available, prop_id)

    def get_specific_details(self) -> Dict:
        return {}


class ResidentialProperty(Property):
    def __init__(self, kind, address=None, floor_area=0.0, rent_amount=0.0,
                 rent_period="monthly", picture_path=None, description="", is_available=True,
                 bedrooms=0, bathrooms=0, prop_id=None):
        super().__init__('residential', kind, address, floor_area, rent_amount,
                        rent_period, picture_path, description, is_available, prop_id)
        self._bedrooms = bedrooms
        self._bathrooms = bathrooms

    def get_specific_details(self) -> Dict:
        return {
            'bedrooms': self._bedrooms,
            'bathrooms': self._bathrooms
        }


class LandProperty(Property):
    def __init__(self, address=None, floor_area=0.0, rent_amount=0.0,
                 rent_period="monthly", picture_path=None, description="", is_available=True,
                 land_use=None, prop_id=None):
        # For land properties, we don't use 'kind', so we pass None
        super().__init__('land', None, address, floor_area, rent_amount,
                        rent_period, picture_path, description, is_available, prop_id)
        self._land_use = land_use

    def get_specific_details(self) -> Dict:
        return {'land_use': self._land_use}


class ResortProperty(Property):
    def __init__(self, kind, address=None, floor_area=0.0, rent_amount=0.0,
                 rent_period="monthly", picture_path=None, description="", is_available=True,
                 amenities=None, prop_id=None):
        super().__init__('resorts', kind, address, floor_area, rent_amount,
                        rent_period, picture_path, description, is_available, prop_id)
        self._amenities = amenities

    def get_specific_details(self) -> Dict:
        return {'amenities': self._amenities}


class VenueProperty(Property):
    def __init__(self, kind, address=None, floor_area=0.0, rent_amount=0.0,
                 rent_period="monthly", picture_path=None, description="", is_available=True,
                 capacity=0, prop_id=None):
        super().__init__('venues', kind, address, floor_area, rent_amount,
                        rent_period, picture_path, description, is_available, prop_id)
        self._capacity = capacity

    def get_specific_details(self) -> Dict:
        return {'capacity': self._capacity}


class Rental:
    PAYMENT_METHODS = ['cash', 'credit_card', 'bank_transfer', 'check']
    PAYMENT_FREQUENCIES = ['monthly', 'yearly']
    
    def __init__(self, client_id, property_id, start_date, end_date, duration_months, 
                 total_amount, payment_method, payment_frequency, next_due_date, status='active', rental_id=None):
        self.client_id = client_id
        self.property_id = property_id
        self.start_date = start_date
        self.end_date = end_date
        self.duration_months = duration_months
        self.total_amount = total_amount
        self.payment_method = payment_method
        self.payment_frequency = payment_frequency
        self.next_due_date = next_due_date
        self.status = status
        self.id = rental_id

    def save(self, db: Database):
        if self.id:
            db.execute(
                """UPDATE rentals SET client_id=?, property_id=?, start_date=?, end_date=?, 
                duration_months=?, total_amount=?, payment_method=?, payment_frequency=?, 
                next_due_date=?, status=? WHERE id=?""",
                (self.client_id, self.property_id, self.start_date, self.end_date,
                 self.duration_months, self.total_amount, self.payment_method, 
                 self.payment_frequency, self.next_due_date, self.status, self.id),
            )
        else:
            cur = db.execute(
                """INSERT INTO rentals (client_id, property_id, start_date, end_date, 
                duration_months, total_amount, payment_method, payment_frequency, next_due_date, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.client_id, self.property_id, self.start_date, self.end_date,
                 self.duration_months, self.total_amount, self.payment_method, 
                 self.payment_frequency, self.next_due_date, self.status),
            )
            self.id = cur.lastrowid
        return self.id


def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Numbers only, please.")


def input_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Enter a valid number.")


def input_date(prompt):
    while True:
        date = input(prompt)
        if not date:
            return None
        try:
            datetime.strptime(date, DATE_FMT)
            return date
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def input_yes_no(prompt):
    while True:
        ans = input(prompt).lower()
        if ans in ["yes", "y"]:
            return True
        elif ans in ["no", "n"]:
            return False
        print("Enter yes or no only.")


def calculate_next_due_date(start_date: str, payment_frequency: str) -> str:
    """Calculate next due date based on start date and payment frequency"""
    start_date_obj = datetime.strptime(start_date, DATE_FMT)
    
    if payment_frequency == "monthly":
        # Add one month to start date
        next_month = start_date_obj.month + 1
        year = start_date_obj.year
        if next_month > 12:
            next_month = 1
            year += 1
        next_due = datetime(year, next_month, start_date_obj.day)
    else:  # yearly
        # Add one year to start date
        next_due = datetime(start_date_obj.year + 1, start_date_obj.month, start_date_obj.day)
    
    return next_due.strftime(DATE_FMT)


def next_due_date(paid_on_str: str, frequency: str):
    paid = datetime.strptime(paid_on_str, DATE_FMT)
    if frequency == "monthly":
        month = paid.month + 1
        year = paid.year + (month > 12)
        month = 1 if month > 12 else month
        return datetime(year, month, paid.day).strftime(DATE_FMT)
    elif frequency == "annual":
        return datetime(paid.year + 1, paid.month, paid.day).strftime(DATE_FMT)


def record_payment(db: Database, client_id, property_id, amount, paid_on, freq, notes=None):
    nd = next_due_date(paid_on, freq)
    db.execute(
        "INSERT INTO payments (client_id,property_id,amount,paid_on,frequency,next_due,notes) VALUES (?,?,?,?,?,?,?)",
        (client_id, property_id, amount, paid_on, freq, nd, notes),
    )
    print(f"Payment saved. Next due date: {nd}")


def check_due_payments(db: Database):
    today = datetime.today().strftime(DATE_FMT)
    rows = db.query(
        "SELECT p.id,c.name,p.amount,p.next_due,p.frequency "
        "FROM payments p JOIN clients c ON p.client_id=c.id "
        "WHERE p.next_due<=?",
        (today,),
    )
    if not rows:
        print("No due payments.")
        return
    print("\nDue or Past Due Payments:")
    for r in rows:
        print(f"Client: {r['name']} | Amount: ₱{r['amount']} | Due: {r['next_due']} | {r['frequency']}")


def print_properties(props):
    if not props:
        print("No properties found.")
        return

    print("\nProperties:")
    print("-" * 120)
    for r in props:
        # Create appropriate property object based on category
        category = r['category']
        if category == 'commercial':
            prop = CommercialProperty(r['kind'], r['address'], r['floor_area'], r['rent_amount'],
                                    r['rent_period'], r['picture_path'], r['description'], bool(r['is_available']),
                                    r['id'])
        elif category == 'residential':
            prop = ResidentialProperty(r['kind'], r['address'], r['floor_area'], r['rent_amount'],
                                     r['rent_period'], r['picture_path'], r['description'], bool(r['is_available']),
                                     r['bedrooms'] or 0, r['bathrooms'] or 0, r['id'])
        elif category == 'land':
            prop = LandProperty(r['address'], r['floor_area'], r['rent_amount'],
                              r['rent_period'], r['picture_path'], r['description'], bool(r['is_available']),
                              r['land_use'], r['id'])
        elif category == 'resorts':
            prop = ResortProperty(r['kind'], r['address'], r['floor_area'], r['rent_amount'],
                                r['rent_period'], r['picture_path'], r['description'], bool(r['is_available']),
                                r['amenities'], r['id'])
        elif category == 'venues':
            prop = VenueProperty(r['kind'], r['address'], r['floor_area'], r['rent_amount'],
                               r['rent_period'], r['picture_path'], r['description'], bool(r['is_available']),
                               r['capacity'] or 0, r['id'])
        else:
            continue
            
        print(prop.display_info())
        print(prop.get_picture_info())
        if r['description']:
            print(f"Description: {r['description']}")
        print("-" * 80)
    print("-" * 120)


def upload_picture_interactive(property_id: int) -> str:
    """Interactive method to upload a picture for a property"""
    print(f"\n=== Upload Picture for Property ID: {property_id} ===")
    
    # Show supported formats
    supported_formats = PictureManager.list_supported_formats()
    print(f"Supported picture formats: {', '.join(supported_formats)}")
    print("Example: C:/Users/YourName/Pictures/property.jpg")
    print("Or: /home/username/Pictures/property.png")
    
    while True:
        source_path = input("Enter the full path to the picture file: ").strip()
        
        if not source_path:
            print("No path provided. Picture upload cancelled.")
            return None
        
        # Check if file exists
        if not os.path.exists(source_path):
            print("File not found. Please check the path and try again.")
            continue
        
        # Check file extension
        _, extension = os.path.splitext(source_path.lower())
        if extension not in supported_formats:
            print(f"Unsupported file format. Please use: {', '.join(supported_formats)}")
            continue
        
        try:
            # Upload the picture
            new_path = PictureManager.upload_picture(property_id, source_path)
            print(f"Picture uploaded successfully: {os.path.basename(new_path)}")
            return new_path
        except Exception as e:
            print(f"Error uploading picture: {e}")
            return None


def delete_property_interactive(db: Database):
    """Interactive method to delete a property"""
    print("\n=== Delete Property ===")
    
    # Display all properties
    props = db.query("SELECT * FROM properties ORDER BY id")
    if not props:
        print("No properties found to delete.")
        return
    
    print_properties(props)
    
    try:
        property_id = input_int("\nEnter the ID of the property to delete: ")
        
        # Check if property exists
        prop = db.query("SELECT * FROM properties WHERE id = ?", (property_id,))
        if not prop:
            print(f"Property with ID {property_id} not found.")
            return
        
        # Check if property is currently rented
        rental = db.query("SELECT * FROM rentals WHERE property_id = ? AND status = 'active'", (property_id,))
        if rental:
            print("Cannot delete property that is currently rented!")
            print("Please end the rental first or contact the administrator.")
            return
        
        # Confirm deletion
        prop_details = prop[0]
        print(f"\nProperty to delete:")
        print(f"ID: {prop_details['id']} | {prop_details['kind'] or 'Land'} in {prop_details['address']}")
        print(f"Category: {prop_details['category']} | Rent: ₱{prop_details['rent_amount']}/{prop_details['rent_period']}")
        
        confirm = input_yes_no("\nAre you sure you want to delete this property? This action cannot be undone! (yes/no): ")
        
        if confirm:
            # Delete associated picture
            PictureManager.delete_picture(property_id)
            
            # Delete property from database
            db.execute("DELETE FROM properties WHERE id = ?", (property_id,))
            
            # Delete associated payments
            db.execute("DELETE FROM payments WHERE property_id = ?", (property_id,))
            
            print(f"Property with ID {property_id} has been deleted successfully.")
        else:
            print("Deletion cancelled.")
            
    except ValueError:
        print("Invalid input! Please enter a valid property ID.")


def add_property_interactive(db: Database):
    """Interactive method to add a new property with category-specific details"""
    print("\n=== Add New Property ===")
    
    # Get category
    categories = ['commercial', 'residential', 'land', 'resorts', 'venues']
    print("Available categories: commercial, residential, land, resorts, venues")
    
    category = input("Enter category: ").strip().lower()
    if category not in categories:
        print("Invalid category!")
        return
    
    # Common property details
    address = input("Enter address: ").strip()
    floor_area = input_float("Enter floor area (sqm): ")
    
    # Get both yearly and monthly rent amounts
    rent_amount_yearly = input_float("Enter yearly rent amount: ")
    rent_amount_monthly = input_float("Enter monthly rent amount: ")
    
    print("Rent periods: monthly, yearly")
    rent_period = input("Enter rent period: ").strip().lower()
    if rent_period not in Property.RENT_PERIODS:
        print("Invalid rent period!")
        return
    
    # Use the appropriate rent amount based on selected period
    if rent_period == 'yearly':
        rent_amount = rent_amount_yearly
    else:  # monthly
        rent_amount = rent_amount_monthly
    
    description = input("Enter description of property: ").strip()
    
    # Category-specific details
    if category == 'commercial':
        kind = input("Enter kind (e.g., office, warehouse, retail space, etc.): ").strip()
        prop = CommercialProperty(kind, address, floor_area, rent_amount, rent_period, 
                                None, description, True)
    
    elif category == 'residential':
        kind = input("Enter kind (e.g., apartment, house, condo, etc.): ").strip()
        bedrooms = input_int("Enter number of bedrooms: ")
        bathrooms = input_int("Enter number of bathrooms: ")
        prop = ResidentialProperty(kind, address, floor_area, rent_amount, rent_period,
                                 None, description, True, bedrooms, bathrooms)
    
    elif category == 'land':
        # For land properties, we don't ask for 'kind'
        land_use = input("Enter land use (agricultural, residential, commercial, etc.): ").strip()
        prop = LandProperty(address, floor_area, rent_amount, rent_period,
                          None, description, True, land_use)
    
    elif category == 'resorts':
        kind = input("Enter kind (e.g., beach resort, mountain resort, etc.): ").strip()
        amenities = input("Enter amenities (pool, gym, spa, etc.): ").strip()
        prop = ResortProperty(kind, address, floor_area, rent_amount, rent_period,
                            None, description, True, amenities)
    
    elif category == 'venues':
        kind = input("Enter kind (e.g., wedding venue, conference hall, etc.): ").strip()
        capacity = input_int("Enter capacity: ")
        prop = VenueProperty(kind, address, floor_area, rent_amount, rent_period,
                           None, description, True, capacity)
    
    # Save property first to get ID
    prop.save(db)
    print(f"Property added successfully with ID: {prop.id}")
    
    # Ask about picture upload
    upload_pic = input_yes_no("Do you want to upload a picture for this property? (yes/no): ")
    if upload_pic:
        picture_path = upload_picture_interactive(prop.id)
        if picture_path:
            # Update property with picture path
            prop._picture_path = picture_path
            prop.save(db)
            print("Picture linked to property successfully!")
        else:
            print("Picture upload failed or was cancelled.")


def display_clients_with_rentals(db: Database):
    """Display all clients with their rental and property information"""
    print("\n=== All Clients with Rentals ===")
    
    query = """
        SELECT 
            c.id as client_id, 
            c.name as client_name, 
            c.email as client_email, 
            c.phone as client_phone, 
            c.address as client_address, 
            c.notes as client_notes,
            p.id as property_id, 
            p.category as property_category,
            p.kind as property_kind, 
            p.address as property_address, 
            p.floor_area as property_floor_area,
            p.rent_amount as property_rent_amount, 
            p.rent_period as property_rent_period,
            p.description as property_description,
            r.start_date as rental_start_date,
            r.end_date as rental_end_date, 
            r.payment_frequency as payment_frequency,
            r.next_due_date as next_due_date,
            r.status as rental_status
        FROM clients c
        LEFT JOIN rentals r ON c.id = r.client_id
        LEFT JOIN properties p ON r.property_id = p.id
        ORDER BY c.name
    """
    
    rows = db.query(query)
    
    if not rows:
        print("No clients found.")
        return
    
    current_client = None
    for row in rows:
        client_id = row['client_id']
        
        if current_client != client_id:
            if current_client is not None:
                print()
            current_client = client_id
            print(f"Client: {row['client_name']} | Email: {row['client_email'] or 'N/A'} | Address: {row['client_address'] or 'N/A'}")
            if row['client_phone']:
                print(f"Phone: {row['client_phone']}")
        
        # Check if client has rentals (property_id will be None if no rentals)
        if row['property_id'] is not None:  
            print(f"  - Rented Property: {row['property_kind'] or 'Land'} in {row['property_address']}")
            print(f"    Category: {row['property_category']} | Floor Area: {row['property_floor_area']} sqm")
            print(f"    Rent: ₱{row['property_rent_amount']}/{row['property_rent_period']}")
            print(f"    Rental Period: {row['rental_start_date']} to {row['rental_end_date']}")
            print(f"    Payment Frequency: {row['payment_frequency']}")
            print(f"    Next Due Date: {row['next_due_date']}")
            print(f"    Status: {row['rental_status']}")


def rent_property_interactive(db: Database):
    """Interactive method to rent a property"""
    print("\n=== Rent a Property ===")
    
    # Display available properties
    available_props = db.query("SELECT * FROM properties WHERE is_available=1")
    
    if not available_props:
        print("No available properties found.")
        return
    
    print("\nAvailable Properties:")
    print("-" * 80)
    for i, prop in enumerate(available_props, 1):
        property_name = f"{prop['kind'] or 'Land'} in {prop['address']}"
        print(f"{i}. {property_name} - ₱{prop['rent_amount']}/{prop['rent_period']}")
    print("-" * 80)
    
    # Select property
    try:
        choice = int(input("\nSelect property number: ")) - 1
        if choice < 0 or choice >= len(available_props):
            print("Invalid property selection!")
            return
    except ValueError:
        print("Invalid input!")
        return
    
    selected_prop = available_props[choice]
    print(f"\nSelected Property:")
    
    # Display property details based on category
    if selected_prop['category'] == 'commercial':
        prop_obj = CommercialProperty(selected_prop['kind'], selected_prop['address'], 
                                    selected_prop['floor_area'], selected_prop['rent_amount'],
                                    selected_prop['rent_period'], selected_prop['picture_path'],
                                    selected_prop['description'], True, selected_prop['id'])
    elif selected_prop['category'] == 'residential':
        prop_obj = ResidentialProperty(selected_prop['kind'], selected_prop['address'], 
                                     selected_prop['floor_area'], selected_prop['rent_amount'],
                                     selected_prop['rent_period'], selected_prop['picture_path'],
                                     selected_prop['description'], True, selected_prop['bedrooms'] or 0, 
                                     selected_prop['bathrooms'] or 0, selected_prop['id'])
    elif selected_prop['category'] == 'land':
        prop_obj = LandProperty(selected_prop['address'], selected_prop['floor_area'], selected_prop['rent_amount'],
                              selected_prop['rent_period'], selected_prop['picture_path'],
                              selected_prop['description'], True, selected_prop['land_use'], selected_prop['id'])
    elif selected_prop['category'] == 'resorts':
        prop_obj = ResortProperty(selected_prop['kind'], selected_prop['address'], 
                                selected_prop['floor_area'], selected_prop['rent_amount'],
                                selected_prop['rent_period'], selected_prop['picture_path'],
                                selected_prop['description'], True, selected_prop['amenities'], selected_prop['id'])
    elif selected_prop['category'] == 'venues':
        prop_obj = VenueProperty(selected_prop['kind'], selected_prop['address'], 
                               selected_prop['floor_area'], selected_prop['rent_amount'],
                               selected_prop['rent_period'], selected_prop['picture_path'],
                               selected_prop['description'], True, selected_prop['capacity'] or 0, selected_prop['id'])
    
    print(prop_obj.display_info())
    print(prop_obj.get_picture_info())
    if selected_prop['description']:
        print(f"Description: {selected_prop['description']}")
    
    # Get client information
    print("\nClient Information:")
    name = input("Enter client name: ").strip()
    email = input("Enter client email: ").strip()
    address = input("Enter client address: ").strip()
    phone = input("Enter client phone (optional): ").strip()
    
    # Create client
    client = Client(name, email, phone, address)
    client.save(db)
    
    # Get rental dates
    print("\nRental Period Information:")
    start_date = input_date("Enter start date (YYYY-MM-DD): ")
    if not start_date:
        print("Start date is required!")
        return
    
    end_date = input_date("Enter end date (YYYY-MM-DD): ")
    if not end_date:
        print("End date is required!")
        return
    
    # Validate dates
    start_date_obj = datetime.strptime(start_date, DATE_FMT)
    end_date_obj = datetime.strptime(end_date, DATE_FMT)
    
    if start_date_obj >= end_date_obj:
        print("End date must be after start date!")
        return
    
    # Calculate duration in months
    duration_months = (end_date_obj.year - start_date_obj.year) * 12 + (end_date_obj.month - start_date_obj.month)
    if end_date_obj.day > start_date_obj.day:
        duration_months += 1
    
    if duration_months <= 0:
        print("Rental duration must be at least 1 month!")
        return
    
    # Calculate total amount
    if selected_prop['rent_period'] == 'monthly':
        total_amount = selected_prop['rent_amount'] * duration_months
    else:  # yearly
        total_amount = (selected_prop['rent_amount'] / 12) * duration_months
    
    # Get payment method
    payment_methods = Rental.PAYMENT_METHODS
    print("Payment methods:", ", ".join(payment_methods))
    payment_method = input("Enter payment method: ").strip().lower()
    if payment_method not in payment_methods:
        print("Invalid payment method!")
        return
    
    # Get payment frequency
    print("Payment frequencies: monthly, yearly")
    payment_frequency = input("Enter payment frequency: ").strip().lower()
    if payment_frequency not in Rental.PAYMENT_FREQUENCIES:
        print("Invalid payment frequency!")
        return
    
    # Calculate next due date based on start date and payment frequency
    next_due_date = calculate_next_due_date(start_date, payment_frequency)
    
    # Confirm rental
    print(f"\nRental Summary:")
    print(f"Total Amount: ₱{total_amount:.2f}")
    print(f"Duration: {duration_months} months")
    print(f"From: {start_date} to {end_date}")
    print(f"Payment Frequency: {payment_frequency}")
    print(f"Next Due Date: {next_due_date}")
    confirm = input("\nConfirm rental? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        # Create rental
        rental = Rental(client.id, selected_prop['id'], start_date, end_date,
                      duration_months, total_amount, payment_method, payment_frequency, next_due_date)
        rental.save(db)
        
        # Update property availability
        db.execute("UPDATE properties SET is_available=0 WHERE id=?", (selected_prop['id'],))
        
        print("Property rented successfully!")
    else:
        print("Rental cancelled.")


def display_rentals(db: Database):
    """Display currently rented properties"""
    print("\n=== Currently Rented Properties ===")
    
    query = """
        SELECT p.*, c.name as client_name, r.start_date, r.end_date, r.payment_frequency, r.next_due_date
        FROM properties p
        JOIN rentals r ON p.id = r.property_id
        JOIN clients c ON r.client_id = c.id
        WHERE p.is_available = 0 AND r.status = 'active'
    """
    
    rows = db.query(query)
    
    if not rows:
        print("No currently rented properties.")
        return
    
    for row in rows:
        property_name = f"{row['kind'] or 'Land'} in {row['address']}"
        print(f"Property: {property_name}")
        print(f"Category: {row['category']} | Floor Area: {row['floor_area']} sqm")
        print(f"Rent: ₱{row['rent_amount']}/{row['rent_period']}")
        print(f"Rented by: {row['client_name']}")
        print(f"Rental Period: {row['start_date']} to {row['end_date']}")
        print(f"Payment Frequency: {row['payment_frequency']}")
        print(f"Next Due Date: {row['next_due_date']}")
        
        end_date_obj = datetime.strptime(row['end_date'], DATE_FMT)
        remaining_days = (end_date_obj - datetime.today()).days
        print(f"Remaining Days: {remaining_days}")
        print("-" * 60)


def display_due_payments(db: Database):
    """Display rentals due in 1 month or less"""
    print("\n=== Due Payments (Within 1 Month) ===")
    
    one_month_later = (datetime.today() + timedelta(days=30)).strftime(DATE_FMT)
    
    query = """
        SELECT r.*, c.name as client_name, p.address, p.rent_amount, p.kind
        FROM rentals r
        JOIN clients c ON r.client_id = c.id
        JOIN properties p ON r.property_id = p.id
        WHERE r.next_due_date <= ? AND r.status = 'active'
        ORDER BY r.next_due_date
    """
    
    rows = db.query(query, (one_month_later,))
    
    if not rows:
        print("No due payments in the next month.")
        return
    
    for row in rows:
        next_due_obj = datetime.strptime(row['next_due_date'], DATE_FMT)
        days_remaining = (next_due_obj - datetime.today()).days
        
        print(f"Rental ID: {row['id']}")
        print(f"Client: {row['client_name']}")
        property_name = f"{row['kind'] or 'Land'} in {row['address']}"
        print(f"Property: {property_name}")
        print(f"Next Due Date: {row['next_due_date']} (in {days_remaining} days)")
        print(f"Total Amount: ₱{row['total_amount']:.2f}")
        print(f"Payment Method: {row['payment_method']}")
        print(f"Payment Frequency: {row['payment_frequency']}")
        print("-" * 60)


def menu():
    db = Database()
    try:
        while True:
            print("\n=== Property Leasing System ===")
            print("1) Clients - View all clients with rentals")
            print("2) Properties - View by category & Add property")
            print("3) Rent - Rent a property")
            print("4) Rentals - View currently rented properties")
            print("5) Due Payments - View payments due in 1 month")
            print("6) Exit")

            choice = input("Choose option: ")

            if choice == "1":
                display_clients_with_rentals(db)

            elif choice == "2":
                while True:
                    print("\n=== Properties Menu ===")
                    print("1) View Properties by Category")
                    print("2) Add New Property")
                    print("3) View Available Properties")
                    print("4) Delete Property")
                    print("5) Back to Main Menu")
                    
                    sub_choice = input("Choose option: ")
                    
                    if sub_choice == "1":
                        props = db.query("SELECT * FROM properties ORDER BY category, kind")
                        print_properties(props)
                    
                    elif sub_choice == "2":
                        add_property_interactive(db)
                    
                    elif sub_choice == "3":
                        props = db.query("SELECT * FROM properties WHERE is_available=1")
                        print_properties(props)
                    
                    elif sub_choice == "4":
                        delete_property_interactive(db)
                    
                    elif sub_choice == "5":
                        break
                    
                    else:
                        print("Invalid option. Try again.")

            elif choice == "3":
                rent_property_interactive(db)

            elif choice == "4":
                display_rentals(db)

            elif choice == "5":
                display_due_payments(db)

            elif choice == "6":
                print("System closed.")
                break

            else:
                print("Invalid option. Try again.")

    finally:
        db.close()


if __name__ == "__main__":
    menu()