from re import X
from tkinter import Y
import plotly.graph_objects as go
import plotly.offline as pyo
from django.db.models import Sum, Count
from app.threat_management.models import DetectionCounter
from django.utils import timezone
from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class GraphGenerator:
    def __init__(self, user):
        self.user = user
    
    def get_daily_detections(self):
        today = timezone.now()
        start_date = today - timedelta(days=30)
        daily_data = (
            DetectionCounter.objects
            .filter(user=self.user, detection__created_at__gte=start_date)
            .values('detection__created_at__date')
            .annotate(total_count=Sum('count'))
            .order_by('detection__created_at__date')
        )
        return daily_data
        
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

        X = np.arange(len(detection_names)).reshape(-1, 1)
        y = np.array(counts)
        model = LinearRegression()
        model.fit(X, y)

        X_future = np.array([len(detection_names)]).reshape(-1, 1)
        y_pred = model.predict(X_future)

        bar_chart = go.Figure()

        bar_chart.add_trace(go.Bar(
            x=detection_names,
            y=counts,
            name='Detecciones reales',
            marker_color='blue',
            hovertemplate='<b>Detección:</b> %{x}<br><b>Cantidad:</b> %{y}<extra></extra>'
        ))

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

        bar_chart.add_trace(go.Bar(
            x=['Predicción'],
            y=y_pred,
            name='Predicción',
            marker_color='red',
            hovertemplate='Se predice la siguiente cantidad de aumento de detecciones: ' + str(round(y_pred[0], 2)) + '<extra></extra>'
        ))

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

        config = {
            'displayModeBar': False
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
        daily_data = self.get_daily_detections()

        if not daily_data:
            return None

        dates = [item['detection__created_at__date'] for item in daily_data]
        counts = [item['total_count'] for item in daily_data]

        X = np.array([(date - dates[0]).days for date in dates]).reshape(-1, 1)  # Asegurarse de que X sea 2D
        Y = np.array(counts)

        poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly_features.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, Y)

        X_future = np.array(range(len(X), len(X) + 7)).reshape(-1, 1)  # Predicción para 7 días más
        X_future_poly = poly_features.transform(X_future)
        y_pred = model.predict(X_future_poly)

        line_chart = go.Figure()

        line_chart.add_trace(go.Scatter(
            x=dates,
            y=counts,
            mode='lines+markers',
            name='Detecciones reales',
            line=dict(color='blue')
        ))

        future_dates = [dates[-1] + timedelta(days=i + 1) for i in range(7)]
        line_chart.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred,
            mode='lines',
            name='Predicciones',
            line=dict(color='red', dash='dash')
        ))
        
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

        config = {
            'displayModeBar': False
        }
        return pyo.plot(line_chart, config=config, auto_open=False, include_plotlyjs=False, output_type='div')

    def get_total_threats(self):
        return DetectionCounter.objects.filter(user=self.user).aggregate(total=Sum('count'))['total'] or 0

    def get_threat_types(self):
        return DetectionCounter.objects.filter(user=self.user).values('detection__name').distinct().count()

    def get_next_day_prediction(self):
        daily_data = self.get_daily_detections()
        if not daily_data:
            return 0

        dates = [item['detection__created_at__date'] for item in daily_data]
        counts = [item['total_count'] for item in daily_data]

        if len(dates) < 2:
            return counts[-1] if counts else 0

        X = np.array([(date - dates[0]).days for date in dates]).reshape(-1, 1)
        y = np.array(counts)

        model = LinearRegression()
        model.fit(X, y)

        next_day = X[-1][0] + 1
        prediction = model.predict([[next_day]])[0]
        return round(prediction, 2)

    def get_last_prediction_date(self):
        daily_data = self.get_daily_detections()
        if not daily_data:
            return timezone.now().date()
        return max(item['detection__created_at__date'] for item in daily_data) + timedelta(days=1)

    def get_threat_details(self):
        threat_data = (
            DetectionCounter.objects
            .filter(user=self.user)
            .values('detection__name',  'detection__icon')
            .annotate(total_count=Sum('count'))
            .order_by('-total_count')
        )
        
        total_threats = sum(item['total_count'] for item in threat_data)
        
        return [
            {
                'name': item['detection__name'],
                'icon': item['detection__icon'],
                'count': item['total_count'],
                'percentage': round((item['total_count'] / total_threats) * 100, 2) if total_threats else 0,
                'status': 'Activo' 
            }
            for item in threat_data
        ]
        