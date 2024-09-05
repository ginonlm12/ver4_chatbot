import csv
import os

response = {
    "Name": "Nguyễn Hoàng Lâm",
    "Address": "285 Thanh Nhàn",
    "PhoneNumber": "0916836437",
    "ProductList": [
        {"ProductName": "Điều hòa Daikin 12.000 BTU 2 chiều Inverter - Model 2023", "Price": 11880880.0, "Quantity": '1'},
        {"ProductName": "Điều hòa MDV - Inverter 9.000 BTU", "Price": 6014184.0, "Quantity": '2'}
    ]
}


def write_to_csv(response):
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    csv_filename = r"data\customer_log.csv"
    
    # Writing to the CSV file
    try:
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Address', 'PhoneNumber', 'ProductName', 'Price', 'Quantity'])
            
            for product in response['ProductList']:
                writer.writerow([
                    response['Name'],
                    response['Address'],
                    response['PhoneNumber'],
                    product['ProductName'],
                    product['Price'],
                    product['Quantity']
                ])
        
        print(f"Data successfully written to {csv_filename}")
    
    except PermissionError as e:
        print(f"PermissionError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
