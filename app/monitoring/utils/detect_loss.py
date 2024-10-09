import os
import pandas as pd
import cv2
from datetime import datetime
from dotenv import load_dotenv
from AWSrekonection.src.main import ImageProcessor
from AWSrekonection.src.reconocimiento import RekognitionService
from app.alarm.models import Alarm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import time
from dash import Dash, dcc, html, Input, Output
import plotly.express as px



# Cargar las variables de entorno
load_dotenv()

# Inicializar el servicio de Rekognition
rekognition_service = RekognitionService()
image_processor = ImageProcessor()

# Inicializa la captura de video
cap = cv2.VideoCapture(0)

# Clases de amenazas a detectar
detected_classes = ['Firearm', 'Mobile Phone', 'Laptop', 'Glasses', 'Handbag', 'Person']
log_file = 'detections.csv'

# Asegúrate de que el archivo de registro existe
if not os.path.isfile(log_file):
    with open(log_file, 'w') as f:
        f.write('timestamp,class,confidence\n')  # Encabezados del CSV

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

app = Dash(_name_)

app.layout = html.Div([
    html.H1("Detección de Amenazas"),
    dcc.Graph(id='graph'),
    dcc.Dropdown(
        id='timeframe-dropdown',
        options=[
            {'label': 'Diario', 'value': 'D'},
            {'label': 'Semanal', 'value': 'W'},
            {'label': 'Mensual', 'value': 'M'}
        ],
        value='M',  # Valor predeterminado
        clearable=False
    ),
    html.Button('Iniciar Detección', id='start-button', n_clicks=0),
    html.Div(id='output-container', style={'margin-top': '20px'})
])

@app.callback(
    Output('graph', 'figure'),
    Output('output-container', 'children'),
    Input('timeframe-dropdown', 'value'),
    Input('start-button', 'n_clicks')
)
def update_graph(timeframe, n_clicks):
    global last_email_time

    if n_clicks > 0:
        # Registra la detección de objetos en tiempo real
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convierte el frame a bytes
            _, buffer = cv2.imencode('.jpg', frame)
            image_bytes = buffer.tobytes()

            # Detecta objetos en el frame
            labels = image_processor.detect_objects(image_bytes)

            # Filtra y muestra las etiquetas relevantes
            results = image_processor.filter_detected_classes(labels, detected_classes)

            # Registra las detecciones y dibuja las etiquetas en el video
            for name, confidence in results:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(log_file, 'a') as f:
                    f.write(f'{timestamp},{name},{confidence:.2f}\n')  # Registra la detección
                
                # Si se detecta un objeto sospechoso, activar alarma y enviar correo
                if confidence > 0.5:  # Cambiar por tu umbral
                    alarm = Alarm.objects.filter(is_active=True).first()
                    if alarm:
                        alarm.activate()
                    else:
                        default_alarm = Alarm()
                        default_alarm.play_default_alarm()

                    current_time = time.time()
                    if current_time - last_email_time > EMAIL_COOLDOWN:
                        send_alert_email(frame)
                        last_email_time = current_time
            
            # Muestra el frame (descomentar para ver la cámara)
            cv2.imshow('Detección de Objetos', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Análisis de los datos registrados
        data = pd.read_csv(log_file, parse_dates=['timestamp'])
        data['date'] = data['timestamp'].dt.date  # Extrae la fecha

        # Cuenta las detecciones según el intervalo de tiempo seleccionado
        if timeframe == 'D':
            counts = data.groupby(['date', 'class']).size().reset_index(name='counts')
        elif timeframe == 'W':
            counts = data.groupby([data['timestamp'].dt.to_period('W'), 'class']).size().reset_index(name='counts')
            counts['date'] = counts['timestamp'].dt.to_timestamp()
        else:  # 'M'
            counts = data.groupby([data['timestamp'].dt.to_period('M'), 'class']).size().reset_index(name='counts')
            counts['date'] = counts['timestamp'].dt.to_timestamp()

        # Gráfico de las detecciones
        fig = px.bar(counts, x='date', y='counts', color='class', title='Detecciones de Amenazas')
        return fig, "Detecciones registradas. Presione 'Iniciar Detección' para continuar."

    return {}, "Presione 'Iniciar Detección' para empezar."

def send_alert_email(frame):
    context = {
        'alert': 'Se ha detectado un comportamiento sospechoso.',
    }

    html_content = render_to_string('emails/suspicious_behavior_alert.html', context)
    text_content = strip_tags(html_content)

    subject = f'Alerta de seguridad'
    from_email = settings.EMAIL_HOST_USER
    to = ['duranalexis879@gmail.com']

    _, buffer = cv2.imencode('.jpg', frame)
    image_content = buffer.tobytes()

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.attach('sospechoso_detectado.jpg', image_content, 'image/jpeg')

    msg.send(fail_silently=False)


if _name_ == '_main_':
    app.run_server(debug=True)

# Libera la captura y cierra las ventanas al final
cap.release()
cv2.destroyAllWindows()