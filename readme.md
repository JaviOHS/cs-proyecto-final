# PASYS ALERT

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg) ![Django](https://img.shields.io/badge/django-5.1%2B-green.svg)

Sistema de videovigilancia inteligente para la detección de múltiples amenazas mediante procesamiento de imágenes y análisis en tiempo real.

## 🚀 Características

- Detección de amenazas en tiempo real
- Integración con AWS Rekognition
- Sistema de alertas por correo electrónico
- Interfaz responsiva con TailwindCSS
- Panel de administración integrado
- Análisis de video mediante IA

## 📋 Prerrequisitos

- Python 3.8 o superior
- Node.js y npm
- Cuenta de AWS con acceso a S3 y Rekognition
- Cuenta y credencial de OpenAI para funcionalidades de Chatbot

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/JaviOHS/cs-proyecto-final.git
cd cs-proyecto-final
```

### 2. Configurar el entorno virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/MacOS
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configuración del entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Django
SECRET_KEY=tu_clave_secreta
DEBUG=False

# AWS
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_STORAGE_BUCKET_NAME=nombre_bucket
AWS_S3_REGION_NAME=region

# Email
EMAIL_HOST_USER=tu_email
EMAIL_HOST_PASSWORD=tu_password

# OpenAI
OPENAI_API_KEY=tu_api_key
```

Alternativamente, estas variables pueden configurarse en `settings.py`.

### 5. Configurar la base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

> **Nota**: Al realizar las migraciones se crearán automáticamente dos usuarios por defecto (cliente y administrador).

### 6. Configurar TailwindCSS
```bash
cd static/tailwind
npm install
npm run watch
```

## 🚀 Ejecución

### Desarrollo con Live Reload (opcional)
```bash
python manage.py livereload
```

### Servidor de desarrollo
```bash
python manage.py runserver
```

Visita `http://localhost:8000` en tu navegador.

## 👥 Usuarios por defecto

| Tipo    | Usuario           | Correo Electrónico         | Contraseña       |
|---------|-------------------|----------------------------|------------------|
| Administrador   | Javicho           | javicho@pasysalert.com        | secret_password  |
| Cliente | RamónPA_  | ramon@pasysalert.com          | secret_password  |

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - mira el archivo [LICENSE.md](LICENSE.md) para detalles.

## 📧 Contacto

- JaviOHS - jharos@unemi.edu.ec

- AlexisJr2004 - snietod@unemi.edu.ec

- Link del proyecto: [https://github.com/JaviOHS/cs-proyecto-final](https://github.com/JaviOHS/cs-proyecto-final)

