from PIL import Image
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="El número de celular debe ingresarse en el formato: '+999999999'. Hasta 15 dígitos permitidos."
)

def validate_dni(value):
    cedula = str(value)
    if not cedula.isdigit():
        raise ValidationError('La cédula debe contener solo números.')

    longitud = len(cedula)
    if longitud != 10:
        raise ValidationError('Cantidad de dígitos incorrecta.')

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i in range(9):
        digito = int(cedula[i])
        coeficiente = coeficientes[i]
        producto = digito * coeficiente
        if producto > 9:
            producto -= 9
        total += producto

    digito_verificador = (total * 9) % 10
    if digito_verificador != int(cedula[9]):
        raise ValidationError('La cédula no es válida.')


def validate_image(image_field):
    """
    Valida el formato de la imagen. Solo se permiten JPG, PNG y GIF.
    """
    if not image_field or isinstance(image_field, str):  
        return
    valid_extensions = ['jpg', 'jpeg', 'png']
    extension = image_field.name.split('.')[-1].lower()

    if extension not in valid_extensions:
        raise ValidationError("Formato de imagen no válido. Solo se permiten JPG, PNG y GIF.")

def resize_image(image_path, size):
    """
    Recorta y redimensiona la imagen al tamaño dado, manteniendo la parte central,
    y la guarda en el mismo path.
    """
    with Image.open(image_path) as img:
        # Obtener las dimensiones originales
        width, height = img.size
        
        # Determinar el lado más corto
        min_side = min(width, height)
        
        # Calcular las coordenadas para el recorte
        left = (width - min_side) / 2
        top = (height - min_side) / 2
        right = (width + min_side) / 2
        bottom = (height + min_side) / 2
        
        # Recortar la imagen
        img_cropped = img.crop((left, top, right, bottom))
        
        # Redimensionar la imagen recortada
        img_resized = img_cropped.resize(size, Image.LANCZOS)
        
        # Guardar la imagen recortada y redimensionada
        img_resized.save(image_path)
