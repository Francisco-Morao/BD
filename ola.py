from datetime import datetime

def confirma_data(data):
    try:
        data_obj = datetime.strptime(data, "%Y-%m-%d")
        
        if data_obj.year in [2023, 2024]:
            return True
        else:
            return False
    except ValueError:
        return False

print(confirma_data("2023-13-01"))  # Deve retornar True
print(confirma_data("2023-12-32"))  # Deve retornar False
print(confirma_data("2024-05-25"))  # Deve retornar True
print(confirma_data("invalid-date"))  # Deve retornar False