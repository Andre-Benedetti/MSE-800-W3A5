import sqlite3
from datetime import date
from typing import Set, Dict, List, Tuple

class Patient: #Represents a patient in the clinic.
    
    def __init__(self, patient_id: int, name: str, dob: str, phone: str, address: str):
        self.patient_id = patient_id
        self.name = name
        self.dob = dob  # Format 'YYYY-MM-DD'
        self.phone = phone
        self.address = address
        self.age = _calculate_age(dob)

    def is_senior(self, threshold: int = 65) -> bool: #Checks if the patient is considered a senior
        return self.age > threshold

    def get_info_dict(self) -> Dict: #Returns all patient information as a dictionary 1-to-1
        
        return {
            "ID": self.patient_id,
            "Name": self.name,
            "Date of Birth": self.dob,
            "Age": self.age,
            "Phone": self.phone,
            "Address": self.address
        }

class Specialty: #medical specialty with a unique code
    
    def __init__(self, code: str, name: str):
        self.code = code
        self.name = name

class Doctor: #Doctor can be linked to multiple specialties
    
    def __init__(self, doctor_id: int, name: str, phone: str):
        self.doctor_id = doctor_id
        self.name = name
        self.phone = phone
        # Note: Specialty linkages are handled by the database class

class ClinicDatabase:#Manages database connections and CRUD operations.
    
    def __init__(self, db_name: str = 'clinic_oop_db.sqlite'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establishes a connection to the SQLite database."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def _create_tables(self):#Creates all necessary tables (including junction table).       
        
        # Patients Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Patients (
                patient_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                phone TEXT,
                address TEXT
            )
        """)

        # Doctors Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Doctors (
                doctor_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT
            )
        """)

        # Specialties Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Specialties (
                specialty_code TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        # DoctorSpecialties Table (Junction Table for M:N relationship)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DoctorSpecialties (
                doctor_id INTEGER,
                specialty_code TEXT,
                PRIMARY KEY (doctor_id, specialty_code),
                FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id),
                FOREIGN KEY (specialty_code) REFERENCES Specialties(specialty_code)
            )
        """)

        self.conn.commit()
    
    #CRUD methods for inserting data into tables
    def insert_patient(self, patient: Patient):#Inserts a patient into the Patients table
        sql = "INSERT OR REPLACE INTO Patients (patient_id, name, dob, phone, address) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(sql, (patient.patient_id, patient.name, patient.dob, patient.phone, patient.address))
        self.conn.commit()

    def insert_doctor(self, doctor: Doctor):#Inserts a doctor into the Doctors table
        sql = "INSERT OR REPLACE INTO Doctors (doctor_id, name, phone) VALUES (?, ?, ?)"
        self.cursor.execute(sql, (doctor.doctor_id, doctor.name, doctor.phone))
        self.conn.commit()

    def insert_specialty(self, specialty: Specialty): #Inserts a specialty into the Specialties table
        sql = "INSERT OR REPLACE INTO Specialties (specialty_code, name) VALUES (?, ?)"
        self.cursor.execute(sql, (specialty.code, specialty.name))
        self.conn.commit()

    def assign_doctor_specialty(self, doctor_id: int, specialty_code: str): #Assigns a specialty to a doctor in the junction table
        sql = "INSERT OR IGNORE INTO DoctorSpecialties (doctor_id, specialty_code) VALUES (?, ?)"
        self.cursor.execute(sql, (doctor_id, specialty_code))
        self.conn.commit()

    def get_all_patients(self) -> List[Patient]: #Counts the total number of patients 
        self.cursor.execute("SELECT patient_id, name, dob, phone, address FROM Patients")
        patient_data = self.cursor.fetchall()
        
        patients = []
        for row in patient_data:
            patients.append(Patient(*row))
        return patients

    def count_doctors_by_specialty(self, specialty_code: str) -> Tuple[int, str]: #Counts the total number of distinct doctors linked to a specific specialty code
        
        sql_count = """
            SELECT COUNT(DISTINCT DS.doctor_id)
            FROM DoctorSpecialties DS
            WHERE DS.specialty_code = ?
        """ 
        self.cursor.execute(sql_count, (specialty_code,))
        count = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT name FROM Specialties WHERE specialty_code = ?", (specialty_code,))# Get specialty name for display
        specialty_name = self.cursor.fetchone()
        name = specialty_name[0] if specialty_name else specialty_code
        
        return count, name

    def close(self): #Closes the underlying database connection.
        if self.conn:
            self.conn.close()

def _calculate_age(dob_str: str) -> int: # Function for age calculation based on DOB
    try:
        birth_year = int(dob_str.split('-')[0])
        current_year = date.today().year
        return current_year - birth_year
    except:
        return 0 
    
class Clinic: #High-level clinic operations interfacing
    
    def __init__(self):
        self.db = ClinicDatabase()
    
    def list_senior_patients(self, senior_age_threshold: int = 65): #List full information of all senior patients (> 65 years)
        
        all_patients: List[Patient] = self.db.get_all_patients() 
        senior_patients_found = [
            patient for patient in all_patients
            if patient.is_senior(senior_age_threshold)
        ]

        if not senior_patients_found: #check if any senior patients were found
            print(f"\n--- Senior Patients (Above {senior_age_threshold} years old) ---")
            print("No senior patients found in the database.")
            return

        print(f"\n--- Full List of Senior Patients (Age > {senior_age_threshold}) ---")
        for i, patient in enumerate(senior_patients_found, 1):
            print(f"\n{i}. Patient ID: {patient.patient_id}:")
            info = patient.get_info_dict()
            for key, value in info.items():
                print(f"    - {key}: {value}")
        
   
    def display_ophthalmology_doctor_count(self, specialty_code: str = "OPT"): #Display the total number of doctors who specialize in ophthalmology
        
        count, name = self.db.count_doctors_by_specialty(specialty_code) 

        print(f"\n--- Doctor Count by Specialty ---")
        print(f"Specialty: {name} (Code: {specialty_code})")
        print(f"Total Number of Doctors: {count}")
        return count

    def close(self):        
        self.db.close() #Closes the database connection


def setup_initial_data(clinic: Clinic): #Sets up initial data for testing and demonstration purposes.
    
    # Specialties Data
    clinic.db.insert_specialty(Specialty("OPT", "Ophthalmology"))
    clinic.db.insert_specialty(Specialty("CAR", "Cardiology"))
    clinic.db.insert_specialty(Specialty("GEN", "General Practice"))
    
    # Doctors Data
    dr_ana = Doctor(1, "Dr. Ana Ferreira", "555-1111")
    dr_sofia = Doctor(3, "Dr. Sofia Reis", "555-3333")
    dr_laura = Doctor(5, "Dr. Laura Gomes", "555-5555")
    
    clinic.db.insert_doctor(dr_ana)
    clinic.db.insert_doctor(Doctor(2, "Dr. Bruno Costa", "555-2222"))
    clinic.db.insert_doctor(dr_sofia)
    clinic.db.insert_doctor(Doctor(4, "Dr. Ricardo Nunes", "555-4444"))
    clinic.db.insert_doctor(dr_laura)

    # Assign Specialties
    clinic.db.assign_doctor_specialty(1, "OPT") 
    clinic.db.assign_doctor_specialty(2, "CAR")
    clinic.db.assign_doctor_specialty(3, "OPT")
    clinic.db.assign_doctor_specialty(3, "GEN") # Sofia has two specialties
    clinic.db.assign_doctor_specialty(4, "GEN")
    clinic.db.assign_doctor_specialty(5, "OPT") # Total OPT doctors: 1, 3, 5 (Count: 3)

    # Patients Data
    clinic.db.insert_patient(Patient(101, "Joana Silva", "1955-08-15", "555-1234", "10, Street A")) # Senior (~70)
    clinic.db.insert_patient(Patient(102, "Carlos Mendes", "1990-03-20", "555-5678", "25, Avenue B")) # Not Senior (~35)
    clinic.db.insert_patient(Patient(103, "Helena Souza", "1945-11-01", "555-9012", "30, Road C")) # Senior (~80)
    clinic.db.insert_patient(Patient(104, "Pedro Lima", "2000-05-10", "555-3456", "5, Alley D")) # Not Senior (~25)
    

def main():
    clinic_system = Clinic() 
       
    setup_initial_data(clinic_system) # Set up the data

    clinic_system.list_senior_patients() # List senior patients
    clinic_system.display_ophthalmology_doctor_count("OPT")   # Display ophthalmology doctor count
    clinic_system.close() # Close connection
   
if __name__ == "__main__":
    main()