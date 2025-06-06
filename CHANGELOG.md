## [v0.1.0] - 2025-06-06
- Estructura inicial
- Endpoint POST `/donations` para crear una donación
- Endpoint GET `/donations` para listar donaciones disponibles
- Endpoint GET `/donations/all` para listar todas las donaciones (disponibles e inactivas)
- Endpoint PUT `/donations/<donation_id>` para cambiar la disponibilidad de una donación
- Endpoint DELETE `/donations/<donation_id>` para eliminar una donación
- Soporte para imágenes

## [v0.1.1] - 2025-06-06
### Added
- Nuevo campo `email` en los endpoints:
  - **POST /donations**: Ahora requiere email del donante (campo obligatorio)
  - **GET /donations** y **GET /donations/all**: Incluye email en la respuesta
- Validaciones para email:
  - Formato válido
  - Campo obligatorio
  - Documentación en Swagger actualizada