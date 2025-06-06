import datetime

def validate_donation(data):
    errors = {}

    if not data.get("title"):
        errors["title"] = "Este campo es obligatorio"

    if not data.get("description"):
        errors["description"] = "Este campo es obligatorio"
    
    category = data.get("category")
    condition = data.get("condition")

    general_conditions = ["Usado", "En perfecto estado", "Usado una vez", "Nuevo"]
    food_conditions = ["Perecedero", "No perecedero"]

    if category == "Alimentos":
        if condition not in food_conditions:
            errors["condition"] = "Debe ser 'Perecedero' o 'No perecedero' para alimentos"
    else:
        if condition not in general_conditions:
            errors["condition"] = "Condición no válida para esta categoría"

    # Validar expiration_date solo si es Alimentos
    if category == "Alimentos" and "expiration_date" in data:
        try:
            datetime.datetime.strptime(data["expiration_date"], "%Y-%m-%d")
        except ValueError:
            errors["expiration_date"] = "Formato inválido. Debe ser YYYY-MM-DD"

    location = data.get("location")
    if not location or not isinstance(location, dict):
        errors["location"] = "Debe incluir ciudad (y opcionalmente dirección)"
    else:
        if not location.get("city"):
            errors["city"] = "La ciudad es obligatoria"
        # address es opcional, pero si viene que no esté vacío
        if "address" in location and location["address"] is not None:
            if not location["address"].strip():
                errors["address"] = "La dirección no puede estar vacía si se incluye"

    return errors
