import cv2
import numpy as np
import json
import base64
from io import BytesIO
from PIL import Image
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

class FacialRecognitionView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            base64_image = data.get('image', '')

            if not base64_image:
                return JsonResponse({"success": False, "message": "No se recibió imagen en base64"}, status=400)

            # Decodificar la imagen recibida
            image = self.decode_base64_and_convert_to_image(base64_image)
            if image is None:
                return JsonResponse({"success": False, "message": "Error al decodificar la imagen"}, status=400)

            # Convertir la imagen de entrada en escala de grises
            gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray_image, 1.1, 4)

            if len(faces) == 0:
                return JsonResponse({"success": False, "message": "No se detectó un rostro en la imagen"}, status=400)

            for (x, y, w, h) in faces:
                face_region = gray_image[y:y + h, x:x + w]

                # Comparar con las imágenes de los usuarios
                users = User.objects.exclude(image='')  # Excluye usuarios sin imagen
                for user in users:
                    if user.image:
                        profile_image = Image.open(user.image.path)
                        profile_image_np = np.array(profile_image)
                        gray_profile_image = cv2.cvtColor(profile_image_np, cv2.COLOR_RGB2GRAY)

                        profile_faces = face_cascade.detectMultiScale(gray_profile_image, 1.1, 4)
                        if len(profile_faces) > 0:
                            for (px, py, pw, ph) in profile_faces:
                                profile_face_region = gray_profile_image[py:py + ph, px:px + pw]
                                
                                # Comparar la región de la cara usando correlación normalizada
                                match_result = cv2.matchTemplate(face_region, profile_face_region, cv2.TM_CCOEFF_NORMED)
                                similarity = cv2.minMaxLoc(match_result)[1]

                                if similarity > 0.8:  # Ajustar umbral de similitud
                                    login(request, user)
                                    return JsonResponse({
                                        "success": True,
                                        "message": "Coincidencia facial válida, usuario autenticado",
                                        "redirect": reverse('home')
                                    }, status=200)

            return JsonResponse({"success": False, "message": "No se encontró una coincidencia facial válida"}, status=400)

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error interno: {str(e)}"}, status=500)

    def decode_base64_and_convert_to_image(self, base64_data):
        try:
            image_data = base64_data.split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            image = image.convert('RGB')
            return image
        except Exception:
            return None

class RegisterFaceView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            base64_image = data.get('image', '')

            if not base64_image:
                return JsonResponse({"success": False, "message": "No se recibió imagen en base64"}, status=400)

            user = request.user
            image_data = base64.b64decode(base64_image.split(',')[1])
            user.image.save(f'face_{user.id}.jpg', ContentFile(image_data), save=True)

            return JsonResponse({"success": True, "message": "Imagen facial registrada con éxito"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)