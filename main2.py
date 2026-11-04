from model.EnergyLogger import EnergyLog
from service.CSVParser import CSVParser
from service.ImportManager import ImportManager
# from csv_parser import CSVParser
# from import_manager import ImportManager

def main():
    file_path = "energy_data.csv"
    
    # Initialize the CSVParser
    parser = CSVParser(file_path)

    file_path = "energy_data.csv"

if not os.path.exists(file_path):
    df_sample = pd.DataFrame({
        "room_id": [1, 2, 1],
        "timestamp": ["2026-11-04 10:00:00", "2026-11-04 10:00:00", "2026-11-04 11:00:00"],
        "energy_consumed_kwh": [12.5, 8.3, 10.1],
        "indoor_temp": [21.5, 22.0, 21.0]
    })
    df_sample.to_csv(file_path, index=False)
    print("Created a temporary test 'energy_data.csv' file.")
    
    if parser.validate_csv():
        # Parse the data into EnergyLog objects
        logs = parser.parse_data()
        print(f"Successfully parsed {len(logs)} records.")
        
        # Initialize the ImportManager
        manager = ImportManager(user_id="user_001")
        success = manager.bulk_insert(logs)
        
        if success:
            print(f"Import Status: {manager.get_import_status()}")
            print(f"Total Records Imported: {manager.get_total_imported()}")
        else:
            print("Import failed.")
    else:
        print("CSV validation failed.")

if __name__ == "__main__":
    main()