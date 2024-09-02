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



class FacialRecognitionView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            base64_image = data.get('image', '')

            if not base64_image:
                return JsonResponse({"success": False, "message": "No se recibió imagen en base64"}, status=400)

            image = self.decode_base64_and_convert_to_image(base64_image)
            if image is None:
                return JsonResponse({"success": False, "message": "Error al decodificar la imagen"}, status=400)

            image_np = np.array(image.convert('RGB'))
            image_gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            image_gray_resized = cv2.resize(image_gray, (100, 100))

            user_profiles = UserProfile.objects.all()
            for user_profile in user_profiles:
                if user_profile.image:
                    profile_image = Image.open(user_profile.image.path)
                    profile_image_np = np.array(profile_image.convert('RGB'))
                    profile_image_gray = cv2.cvtColor(profile_image_np, cv2.COLOR_RGB2GRAY)
                    profile_image_gray_resized = cv2.resize(profile_image_gray, (100, 100))

                    # Usa el método de comparación de histogramas
                    similarity = cv2.compareHist(
                        cv2.calcHist([image_gray_resized], [0], None, [256], [0, 256]),
                        cv2.calcHist([profile_image_gray_resized], [0], None, [256], [0, 256]),
                        cv2.HISTCMP_CORREL
                    )

                    # Ajusta este umbral según sea necesario
                    if similarity > 0.7:
                        login(request, user_profile.user)
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
        except Exception as e:
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
            base64_image = data.get('image', '')

            if not base64_image:
                return JsonResponse({"success": False, "message": "No se recibió imagen en base64"}, status=400)

            user_profile = request.user.userprofile
            user_profile.set_face_image(base64_image)

            return JsonResponse({"success": True, "message": "Imagen facial registrada con éxito"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
