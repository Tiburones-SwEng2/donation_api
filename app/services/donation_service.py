from datetime import datetime
from bson import ObjectId
from app import mongo

def create_donation(data, image_url):
    donation = {
        "email": data["email"],
        "title": data["title"],
        "name": data["name"],
        "description": data["description"],
        "category": data["category"],
        "location": {
            "city": data["location"]["city"],
            "address": data["location"]["address"]
        },
        "condition": data["condition"],
        "expiration_date": data.get("expiration_date"),
        "available": data.get("available", True),
        "image_url": image_url,
        "created_at": datetime.utcnow()
    }

    result = mongo.db.donations.insert_one(donation)
    donation["_id"] = str(result.inserted_id)
    return donation

def list_donations(only_available=True):
    query = {"available": True} if only_available else {}
    donations = mongo.db.donations.find(query).sort("created_at", -1)
    return [
        {
            "id": str(d["_id"]),
            "email": d["email"],
            "title": d["title"],
            "name": d["name"],
            "description": d["description"],
            "category": d["category"],
            "condition": d["condition"],
            "expiration_date": d.get("expiration_date"),
            "available": d.get("available", True),
            "city": d["location"]["city"],
            "address": d["location"].get("address"),
            "image_url": d.get("image_url"),
            "created_at": d["created_at"].isoformat()
        } for d in donations
    ]

def delete_donation(donation_id):
    result = mongo.db.donations.delete_one({"_id": ObjectId(donation_id)})
    return result.deleted_count > 0

def set_donation_availability(donation_id, available):
    """
    Explicitly set donation availability
    """
    try:
        result = mongo.db.donations.update_one(
            {"_id": ObjectId(donation_id)},
            {"$set": {"available": available}}
        )
        return result.modified_count > 0
    except:
        return False

def toggle_donation_availability(donation_id):
    donation = mongo.db.donations.find_one({"_id": ObjectId(donation_id)})
    if not donation:
        return False

    current_state = donation.get("available", True)
    mongo.db.donations.update_one(
        {"_id": ObjectId(donation_id)},
        {"$set": {"available": not current_state}}
    )
    return True

def modify_donation(donation_id, data, image_url):
    donation = mongo.db.donations.find_one({"_id": ObjectId(donation_id)})
    data["image_url"] = image_url
    if not donation:
        return False

    mongo.db.donations.update_one(
        {"_id": ObjectId(donation_id)},
        {"$set": data}
    )
    return True

def get_donation_by_id(donation_id):
    """
    Retrieve a single donation by its ID
    """
    try:
        return mongo.db.donations.find_one({"_id": ObjectId(donation_id)})
    except:
        return None
    
def delete_all_donations():
    """
    Elimina todas las donaciones en la base de datos.
    Retorna el número de documentos eliminados.
    """
    result = mongo.db.donations.delete_many({})
    return result.deleted_count
