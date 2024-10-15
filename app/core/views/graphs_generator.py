import plotly.graph_objects as go
import plotly.offline as pyo
from django.db.models import Sum, Count
from app.threat_management.models import DetectionCounter
from django.utils import timezone
from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

def get_daily_detections(user):
    today = timezone.now()
    start_date = today - timedelta(days=30)  # Cambiar el rango de fechas según sea necesario

    # Obtener datos agrupados por día
    daily_data = (
        DetectionCounter.objects
        .filter(user=user, detection__created_at__gte=start_date)
        .values('detection__created_at__date')  # Agrupar por fecha
        .annotate(total_count=Count('count'))  # Contar detecciones por día
        .order_by('detection__created_at__date')
    )
    
    return daily_data

class GraphGenerator:
    def __init__(self, user):
        self.user = user

    def bar_chart_detections(self):
        detection_data = (
            DetectionCounter.objects
            .values('detection__name')
            .annotate(total_count=Sum('count'))
            .filter(user=self.user)
            .order_by('detection__name')
        )

        if not detection_data:
            return None

        detection_names = [item['detection__name'] for item in detection_data]
        counts = [item['total_count'] for item in detection_data]

        # Crear y entrenar el modelo de regresión lineal
        X = np.arange(len(detection_names)).reshape(-1, 1)
        y = np.array(counts)
        model = LinearRegression()
        model.fit(X, y)

        # Generar predicciones
        X_future = np.array([len(detection_names)]).reshape(-1, 1)
        y_pred = model.predict(X_future)

        # Crear el gráfico de barras
        bar_chart = go.Figure()

        # Detecciones reales
        bar_chart.add_trace(go.Bar(
            x=detection_names,
            y=counts,
            name='Detecciones reales',
            marker_color='blue',
            hovertemplate='<b>Detección:</b> %{x}<br><b>Cantidad:</b> %{y}<extra></extra>'
        ))

        # Añadir etiquetas a las barras reales
        for i, count in enumerate(counts):
            bar_chart.add_annotation(
                x=detection_names[i],
                y=count,
                text=str(count),
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-40,
                font=dict(size=10, color='black')
            )

        # Barra de predicción
        bar_chart.add_trace(go.Bar(
            x=['Predicción'],
            y=y_pred,
            name='Predicción',
            marker_color='red',
            hovertemplate='Se predice la siguiente cantidad de aumento de detecciones: ' + str(round(y_pred[0], 2)) + '<extra></extra>'
        ))

        # Etiqueta de la predicción
        bar_chart.add_annotation(
            x='Predicción',
            y=y_pred[0],
            text=str(round(y_pred[0], 2)),
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            font=dict(size=10, color='black')
        )

        bar_chart.update_layout(
            title='Cantidad de Amenazas Detectadas y Predicción',
            xaxis_title='Amenazas',
            yaxis_title='Número de Detecciones',
            template='plotly_white',
            plot_bgcolor='rgba(255, 255, 255, 0)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
            barmode='group',
        )

        # Configuración para deshabilitar la barra de herramientas
        config = {
            'displayModeBar': False  # Deshabilitar la barra de herramientas
        }

        return pyo.plot(bar_chart, config=config, auto_open=False, include_plotlyjs=False, output_type='div')

    def pie_chart_detections(self):
        detection_data = (
            DetectionCounter.objects
            .values('detection__name')
            .annotate(total_count=Sum('count'))
            .filter(user=self.user)
            .order_by('detection__name')
        )

        if not detection_data:
            return None

        detection_names = [item['detection__name'] for item in detection_data]
        counts = [item['total_count'] for item in detection_data]

        pie_chart = go.Figure(data=[go.Pie(
            labels=detection_names,
            values=counts
        )])

        pie_chart.update_layout(
            title='Porcentaje de Amenazas Detectadas',
            template='plotly_white',
            plot_bgcolor='rgba(255, 255, 255, 0)',
            paper_bgcolor='rgba(255, 255, 255, 0)'
        )

        return pyo.plot(pie_chart, auto_open=False, include_plotlyjs=False, output_type='div')
    
    def line_chart_detections_by_day(self):
        daily_data = get_daily_detections(self.user)

        if not daily_data:
            return None

        # Extraer fechas y conteos
        dates = [item['detection__created_at__date'] for item in daily_data]
        counts = [item['total_count'] for item in daily_data]

        # Convertir fechas a números (días desde el inicio)
        X = np.array([(date - dates[0]).days for date in dates]).reshape(-1, 1)
        y = np.array(counts)

        # Crear y entrenar el modelo de regresión polinómica
        poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly_features.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, y)

        # Generar predicciones
        X_future = np.array(range(len(X), len(X) + 7)).reshape(-1, 1)  # Predicción para 7 días más
        X_future_poly = poly_features.transform(X_future)
        y_pred = model.predict(X_future_poly)

        # Crear el gráfico de líneas con datos reales
        line_chart = go.Figure()

        line_chart.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines+markers',
            name='Detecciones reales',
            line=dict(color='blue')
        ))

        # Agregar predicciones al gráfico
        future_dates = [dates[-1] + timedelta(days=i + 1) for i in range(7)]
        line_chart.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred,
            mode='lines',
            name='Predicciones',
            line=dict(color='red', dash='dash')
        ))

        # Anotación con el mensaje de predicción
        line_chart.add_annotation(
            x=future_dates[-1],
            y=y_pred[-1],
            text='Se predice la siguiente cantidad de aumento de detecciones: ' + str(round(y_pred[-1], 2)),
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            font=dict(size=12, color='red')
        )

        line_chart.update_layout(
            title='Detecciones de Amenazas por Día y Predicciones',
            xaxis_title='Fecha',
            yaxis_title='Número de Detecciones',
            template='plotly_white',
            xaxis=dict(tickformat='%Y-%m-%d'),
            plot_bgcolor='rgba(255, 255, 255, 0)',
            paper_bgcolor='rgba(255, 255, 255, 0)'
        )

        # Configuración para deshabilitar la barra de herramientas
        config = {
            'displayModeBar': False  # Deshabilitar la barra de herramientas
        }

        return pyo.plot(line_chart, config=config, auto_open=False, include_plotlyjs=False, output_type='div')
