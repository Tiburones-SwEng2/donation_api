# API REST - Módulo de Publicación de Donaciones

API REST construida con Flask y MongoDB para permitir a los donadores registrar productos disponibles para donación.

## Funcionalidades
- Registro de productos con imagen, categoría y ubicación
- Base de datos NoSQL (MongoDB)
- Carga de imágenes
- Documentación con Swagger
- Gestión completa de donaciones (crear, listar, actualizar, eliminar)
- Validación de datos según categoría del producto

## Requisitos
- Python 3.8+
- MongoDB (local o remoto)
- Pip

## Instalación

```bash
git clone <repo>
cd donations_api
python -m venv venv
source venv/bin/activate # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración
1. Crear un archivo `.env` en la raíz del proyecto con la siguiente configuración:

```env
MONGO_URI=mongodb://localhost:27017/donationsdb
```

2. Crear la carpeta para las imágenes (opcional, se crea automáticamente):

```bash
mkdir uploads
```

## Uso
Iniciar la aplicación:

```bash
python app.py
```

La API estará disponible en `http://localhost:5000` y la documentación Swagger en `http://localhost:5000/apidocs`.

## Endpoints
- POST /donations - Crear una nueva donación
- GET /donations - Listar donaciones disponibles
- GET /donations/all - Listar todas las donaciones (disponibles e inactivas)
- PUT /donations/<donation_id> - Alternar disponibilidad de una donación
- DELETE donations/<donation_id> - Eliminar una donación

## Estructura del Proyecto
donations_api/
├── app/
│   ├── __init__.py          # Configuración de la aplicación
│   ├── routes/
│   │   └── donation_routes.py # Endpoints de la API
│   ├── schemas/
│   │   └── donation_schema.py # Validación de datos
│   ├── services/
│   │   └── donation_service.py # Lógica de negocio
│   └── utils/
│       └── image_handler.py  # Manejo de imágenes
├── uploads/                 # Almacenamiento de imagenes
├── app.py                   # Punto de entrada
├── requirements.txt         # Dependencias
├── README.md                # Este archivo
└── CHANGELOG.md             # Historial de cambios

## Ejemplos
Crear una donación:

```bash
curl -X POST -F "title=Ropa de invierno" -F "description=Variedad de abrigos" -F "category=Ropa" -F "condition=Usado" -F "city=Bogotá" -F "image=@abrigos.jpg" http://localhost:5000/donations
```

Listar donaciones disponibles:

```bash
curl http://localhost:5000/donations
```