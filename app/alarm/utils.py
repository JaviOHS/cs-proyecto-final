from mutagen.mp3 import MP3
from django.core.exceptions import ValidationError

def validate_sound_file(file):
    # Validar tamaño de archivo
    max_size = 10 * 1024 * 1024  # 10MB en bytes
    if file.size > max_size:
        raise ValidationError("El archivo excede el tamaño máximo de 10MB.")

    # Validar formato de archivo
    if not file.name.endswith('.mp3'):
        raise ValidationError("El archivo debe estar en formato MP3.")

    # Validar duración del archivo
    try:
        audio = MP3(file)
        max_duration = 20  # Duración máxima en segundos
        if audio.info.length > max_duration:
            raise ValidationError("La duración del archivo MP3 excede los 20 segundos.")
    except Exception as e:
        raise ValidationError(f"Error al procesar el archivo MP3: {e}")
