from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.utils.token import account_activation_token
from root.settings import EMAIL_HOST_USER


def send_verification(request, user):
    html_content = get_template('apps/auth/email_template.html').render({
        'username': user.username,
        'domain': get_current_site(request),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    email = EmailMessage('subject', html_content, EMAIL_HOST_USER, [user.email], )
    email.content_subtype = 'html'
    response = email.send()
    return response
