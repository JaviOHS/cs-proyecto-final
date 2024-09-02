import os
import cv2
import numpy as np
import json
import base64
from io import BytesIO
from PIL import Image
import socket
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
import logging
from app.core.models import UserProfile
from app.core.views.recuperation_email import User


logger = logging.getLogger(__name__)
User = get_user_model()


class FacialRecognitionView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Obtener datos del cuerpo de la solicitud
            data = json.loads(request.body)
            base64_image = data.get('image', '')

            if not base64_image:
                return JsonResponse({"success": False, "message": "No se recibió imagen en base64"}, status=400)

            # Decodificar y convertir la imagen
            image = self.decode_base64_and_convert_to_image(base64_image)
            if image is None:
                return JsonResponse({"success": False, "message": "Error al decodificar la imagen"}, status=400)

            # Convertir la imagen a un formato que OpenCV puede procesar
            image_np = np.array(image.convert('RGB'))
            image_gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

            # Buscar el perfil del usuario con la imagen facial almacenada
            user_profiles = UserProfile.objects.all()
            for user_profile in user_profiles:
                if user_profile.face_image:
                    profile_image_np = np.frombuffer(user_profile.face_image, dtype=np.uint8)
                    profile_image = cv2.imdecode(profile_image_np, cv2.IMREAD_GRAYSCALE)
                    profile_image = cv2.resize(profile_image, (100, 100))  # Redimensionar si es necesario

                    # Crear el modelo LBPH y entrenarlo con la imagen del perfil
                    recognizer = cv2.face.LBPHFaceRecognizer_create()
                    recognizer.train([profile_image], np.array([0]))

                    # Comparar la imagen recibida con la imagen de perfil
                    image_gray_resized = cv2.resize(image_gray, (100, 100))  # Redimensionar si es necesario
                    label, confidence = recognizer.predict(image_gray_resized)

                    # Ajustar el umbral de confianza según sea necesario
                    threshold = 70  # Ajusta este umbral según la precisión deseada
                    if confidence < threshold:
                        # Iniciar sesión al usuario
                        user = user_profile.user
                        login(request, user)
                        return JsonResponse({"success": True, "message": "Coincidencia facial válida, usuario autenticado"}, status=200)
            
            return JsonResponse({"success": False, "message": "No se encontró una coincidencia facial válida"}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Solicitud JSON inválida"}, status=400)
        except KeyError as e:
            return JsonResponse({"success": False, "message": f"Falta la clave en la solicitud: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error interno: {str(e)}"}, status=500)


    def decode_base64_and_convert_to_image(self, base64_data):
        try:
            image_data = base64_data.split(',')[1]  # Elimina la parte del tipo MIME
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image = image.convert('RGB')  # Asegúrate de que la imagen esté en formato RGB
            return image
        except Exception as e:
            logger.error(f"Error al decodificar o convertir la imagen: {e}")
            return None



class LoginUserView(View):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            if not user_id:
                return JsonResponse({"success": False, "message": "ID de usuario no proporcionado"}, status=400)

            user = get_object_or_404(User, id=user_id)
            login(request, user)
            return JsonResponse({"success": True, "redirect": reverse('home')})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

class RegisterFaceView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image_array = np.array(image.convert('RGB'))
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) != 1:
                return JsonResponse({"success": False, "message": "Se debe detectar exactamente una cara"})
            
            (x, y, w, h) = faces[0]
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (100, 100))
            
            _, buffer = cv2.imencode('.jpg', face)
            user_profile = request.user.userprofile
            user_profile.face_image = buffer.tobytes()  # Almacena la imagen en bytes
            user_profile.save()
            
            return JsonResponse({"success": True, "message": "Imagen facial registrada con éxito"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

