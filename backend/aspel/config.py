import os

# ===========================
# Configuración Aspel ADM API
# ===========================

# URL base de la API
ASPEL_API_URL = os.getenv(
    "ASPEL_API_URL",
    "https://api.aspel.com.mx"
)

# Credenciales
ASPEL_USERNAME = os.getenv(
    "ASPEL_USERNAME",
    ""
)

ASPEL_PASSWORD = os.getenv(
    "ASPEL_PASSWORD",
    ""
)

# Access Key (cuando Aspel la proporcione)
ASPEL_ACCESS_KEY = os.getenv(
    "ASPEL_ACCESS_KEY",
    ""
)

# Empresa (opcional)
ASPEL_EMPRESA = os.getenv(
    "ASPEL_EMPRESA",
    ""
)

# Tiempo máximo de espera
TIMEOUT = 30