from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.models import User
from apps.utils.token import account_activation_token
from root.settings import EMAIL_HOST_USER


@shared_task
def send_to_gmail(email, domain, type):
    print('ACCEPT TASK')
    user = User.objects.get(email=email)
    subject = 'Activate your account'
    message = render_to_string('apps/auth/email_activation_template.html', {
        'username': user,
        'domain': domain,
        'uid': urlsafe_base64_encode(force_bytes(str(user.pk))),
        'token': account_activation_token.make_token(user),
    })

    # from_email = EMAIL_HOST_USER
    recipient_list = [email]

    email = EmailMessage(subject, message, EMAIL_HOST_USER, recipient_list)
    email.content_subtype = 'html'
    result = email.send()
    print('Send to MAIL')
    return result
