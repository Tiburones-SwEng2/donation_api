import os
from werkzeug.utils import secure_filename

def save_image(image, upload_folder):
    if not image:
        return None
    filename = secure_filename(image.filename)
    os.makedirs(upload_folder, exist_ok=True)
    image.save(os.path.join(upload_folder, filename))
    
   
    return f"/uploads/{filename}"
