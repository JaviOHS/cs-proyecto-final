import json
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Chatbot:
    def __init__(self):
        self.training_data = self.load_training_data()

    def load_training_data(self):
        file_path = os.path.join(settings.BASE_DIR, 'chatbot_training_data.json')
        logger.debug(f"Attempting to load training data from: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded training data from {file_path}")
            logger.debug(f"Training data: {data}")
            return data
        except FileNotFoundError:
            logger.error(f"Training data file not found at {file_path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in training data file at {file_path}")
            return []

    def find_best_match(self, user_question):
        logger.debug(f"Received user question: {user_question}")
        if not self.training_data:
            logger.warning("No training data available")
            return "Lo siento, no tengo información disponible en este momento."
        
        best_match = max(self.training_data, key=lambda x: sum(word in user_question.lower() for word in x['question'].lower().split()))
        logger.debug(f"Best match found: {best_match}")
        return best_match['answer']

    def get_response(self, user_message):
        try:
            logger.debug(f"Getting response for message: {user_message}")
            response = self.find_best_match(user_message)
            logger.debug(f"Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}", exc_info=True)
            return "Lo siento, ha ocurrido un error al procesar tu pregunta."