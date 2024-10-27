from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_alert_email(subject, template_name, context, image_content, image_name, recipient_list):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    from_email = settings.EMAIL_HOST_USER
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    if image_content and image_name:
        msg.attach(image_name, image_content, 'image/jpeg')
    msg.send(fail_silently=False)

def send_alert_email_video(subject, template_name, context, recipient_list, attachment_path=None, attachment_name=None):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    from_email = settings.EMAIL_HOST_USER
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    if attachment_path and attachment_name:
        try:
            with open(attachment_path, 'rb') as attachment_file:
                msg.attach(attachment_name, attachment_file.read(), 'video/mp4')
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo adjunto en la ruta {attachment_path}")
    msg.send(fail_silently=False)