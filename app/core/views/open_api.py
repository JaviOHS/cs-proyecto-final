import json
import os
import requests
from django.http import JsonResponse
from django.views import View

class OpenAIChatView(View):
    def post(self, request):
        # Cargar el cuerpo de la solicitud como JSON
        try:
            body = json.loads(request.body)
            messages = body.get('messages')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'
                },
                json={
                    'model': 'gpt-3.5-turbo',
                    'messages': messages,
                }
            )

            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            data = response.json()
            return JsonResponse(data)  # Retorna la respuesta de OpenAI como JSON
        except requests.exceptions.HTTPError as e:
            return JsonResponse({'error': str(e)}, status=500)  # Manejo de errores
