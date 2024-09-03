import os
from django.core.mail import send_mail
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.views import View

User = get_user_model()

class PasswordResetView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'components/password_reset.html', {'title1': 'Recuperar Contraseña'})
    
    def post(self, request, *args, **kwargs):
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            
            # Generar token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Construir el enlace de restablecimiento
            reset_link = request.build_absolute_uri(
                reverse('core:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Obtener la URL de la imagen estática
            web_url = 'http://127.0.0.1:8000/'  # Reemplaza con tu URL real de la aplicación

            # Configurar el asunto y el mensaje del correo
            subject = 'Restablecimiento de Contraseña - PASYS ALERT'

            message = format_html(
                """
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Restablecimiento de Contraseña - PASYS ALERT</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
                        
                        body {{
                            font-family: 'Roboto', Arial, sans-serif;
                            line-height: 1.6;
                            color: #333333;
                            background-color: #f6f9fc;
                            margin: 0;
                            padding: 0;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 40px auto;
                            background-color: #ffffff;
                            border-radius: 12px;
                            overflow: hidden;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        }}
                        .header {{
                            background: linear-gradient(135deg, #0056b3, #00a0e9);
                            color: #ffffff;
                            text-align: center;
                            padding: 40px 20px;
                        }}
                        .logo {{
                            width: 100px;
                            height: auto;
                            margin-bottom: 20px;
                        }}
                        .company-name {{
                            font-size: 32px;
                            font-weight: 700;
                            letter-spacing: 1px;
                            margin: 0;
                        }}
                        .content {{
                            padding: 40px 30px;
                        }}
                        h2 {{
                            color: #0056b3;
                            font-size: 24px;
                            margin-top: 0;
                            margin-bottom: 20px;
                            text-align: center;
                        }}
                        p {{
                            margin-bottom: 20px;
                            font-size: 16px;
                        }}
                        .button {{
                            display: inline-block;
                            padding: 14px 30px;
                            background-color: #0056b3;
                            color: #ffffff !important;
                            text-decoration: none;
                            border-radius: 50px;
                            font-weight: 700;
                            font-size: 16px;
                            text-align: center;
                            transition: all 0.3s ease;
                            margin: 20px 0;
                        }}
                        .button:hover {{
                            background-color: #003d82;
                            transform: translateY(-2px);
                            box-shadow: 0 4px 10px rgba(0,86,179,0.3);
                        }}
                        .footer {{
                            background-color: #f8f8f8;
                            text-align: center;
                            padding: 30px 20px;
                            font-size: 14px;
                            color: #666666;
                        }}
                        .contact-container {{
                            display: flex;
                            justify-content: center;
                            flex-wrap: wrap;
                            margin-top: 30px;
                        }}
                        .contact-section {{
                            flex: 1 1 200px;
                            margin: 10px;
                            text-align: center;
                        }}
                        .section-icon svg {{
                            width: 30px;
                            height: 30px;
                            fill: #0056b3;
                            margin-bottom: 10px;
                        }}
                        .contact-item a {{
                            color: #0056b3;
                            text-decoration: none;
                            transition: color 0.3s ease;
                        }}
                        .contact-item a:hover {{
                            color: #003d82;
                        }}
                        @media only screen and (max-width: 600px) {{
                            .container {{
                                width: 100%;
                                margin: 0;
                                border-radius: 0;
                            }}
                            .content {{
                                padding: 30px 20px;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <img src="https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcShcy1kdTpTBXxMA-0XfsTqZP95UMFiRR3HgsK8yRa5NtBknor2" alt="PASYS ALERT Logo" class="logo">
                            <h1 class="company-name">PASYS ALERT</h1>
                        </div>
                        <div class="content">
                            <h2>Restablecimiento de Contraseña</h2>
                            <p>Estimado usuario,</p>
                            <p>Hemos recibido una solicitud para restablecer la contraseña de su cuenta. Si usted no ha solicitado este cambio, por favor ignore este correo.</p>
                            <p>Para proceder con el restablecimiento, haga clic en el siguiente botón:</p>
                            <div style="text-align: center;">
                                <a href="{reset_link}" class="button">Restablecer Contraseña</a>
                            </div>
                            <p>Por razones de seguridad, este enlace expirará en 24 horas.</p>
                            <p>Si necesita asistencia adicional, no dude en contactarnos.</p>
                            <p>Atentamente,<br><strong>El equipo de PASYS ALERT</strong></p>
                        </div>
                        <div class="footer">
                            <p>Este es un correo automático, por favor no responda a esta dirección.</p>
                            <div class="contact-container">
                                <div class="contact-section">
                                    <div class="section-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>
                                    </div>
                                    <div class="contact-item">
                                        <a href="mailto:support@pasysalert.com">support@pasysalert.com</a>
                                    </div>
                                </div>
                                <div class="contact-section">
                                    <div class="section-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                                    </div>
                                    <div class="contact-item">
                                        <a href="https://www.google.com/maps/place/UNEMI+-+Universidad+Estatal+de+Milagro/@-2.149223,-79.60552,17z/data=!3m1!4b1!4m5!3m4!1s0x902d1edc7183f1e5:0x77206e08da0eb158!8m2!3d-2.1492284!4d-79.6033313" target="_blank">
                                            Ubicación
                                        </a>
                                    </div>
                                </div>
                                <div class="contact-section">
                                    <div class="section-icon">
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z"/></svg>
                                    </div>
                                    <div class="contact-item">
                                        <a href="https://www.pasysalert.com" target="_blank">www.pasysalert.com</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """,
                reset_link=reset_link
            )


            from_email = 'noreply@tuempresa.com'
            recipient_list = [email]

            # Enviar el correo
            send_mail(subject, '', from_email, recipient_list, fail_silently=False, html_message=message)
            
            success_message = f'Se ha enviado un enlace para restablecer tu contraseña a {email}.'
            messages.success(request, success_message)
            return redirect(reverse('security:signin'))
        except User.DoesNotExist:
            error_message = 'El correo no se encuentra registrado.'
            messages.error(request, error_message)
        
        return render(request, 'components/password_reset.html', {'title1': 'Recuperar Contraseña'})

# Añade estas nuevas vistas
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'components/password_reset_confirm.html'
    success_url = reverse_lazy('security:signin')

    def form_valid(self, form):
        template_name = 'components/password_reset_confirm.html'
        success_url = reverse_lazy('core:password_reset_complete')
        success_message = 'Tu contraseña ha sido cambiada exitosamente.'
        messages.success(self.request, success_message)
        return super().form_valid(form)
