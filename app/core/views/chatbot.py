from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from ..chatbot_logic import Chatbot
import json
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chatbot = Chatbot()

    def post(self, request, *args, **kwargs):
        logger.debug("Received POST request to ChatbotView")
        try:
            data = json.loads(request.body)
            logger.debug(f"Received data: {data}")
            user_message = data.get('message', '')
            logger.debug(f"User message: {user_message}")
            bot_response = self.chatbot.get_response(user_message)
            logger.debug(f"Bot response: {bot_response}")
            return JsonResponse({'response': bot_response})
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body", exc_info=True)
            return JsonResponse({'response': 'Error: Invalid request format'}, status=400)
        except Exception as e:
            logger.error(f"Error in ChatbotView: {str(e)}", exc_info=True)
            return JsonResponse({'response': 'Lo siento, ha ocurrido un error.'}, status=500)