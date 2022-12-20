from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.forms import ModelForm, CharField, PasswordInput
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from apps.models import Comment, User, Post, Contact


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio', 'avatar')


class RegisterForm(ModelForm):
    confirm_password = CharField(widget=PasswordInput(attrs={"autocomplete": "current-password"}))

    def clean_password(self):
        password = self.data.get('password')
        confirm_password = self.data.get('confirm_password')
        if confirm_password != password:
            raise ValidationError('Parolni tekshiring!')
        return make_password(password)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password')


class CustomLoginForm(AuthenticationForm):
    def clean_password(self):
        username = self.data.get('username')
        password = self.data.get('password')
        user = User.objects.filter(username=username).first()
        if user and not user.check_password(password):
            raise ValidationError('The password or username did not match')
        return password


#
class CreateCommentForm(ModelForm):
    class Meta:
        model = Comment
        exclude = ()


class CreatePostForm(ModelForm):
    class Meta:
        model = Post
        exclude = ('status', 'author', 'slug', 'views')


class ChangePasswordForm(ModelForm):
    def clean_password(self):
        user = self.instance
        password = self.data.get('password')
        new_password = self.data.get('new_password')
        confirm_password = self.data.get('confirm_password')
        if new_password == confirm_password:
            if user.check_password(password):
                return make_password(new_password)
            raise ValidationError('Old password isn\'t correct!')
        raise ValidationError('New Password did not match!')

    class Meta:
        model = User
        fields = ('password',)


class ResetPasswordForm(ModelForm):

    def clean(self):
        password = self.data.get('password')
        confirm_password = self.data.get('confirm_password')
        if password != confirm_password:
            raise ValidationError('Password did not match!')
        try:
            pk = force_str(urlsafe_base64_decode(self.data.get('user')))
            user = User.objects.get(pk=pk)
        except:
            user = None
        if not user:
            raise ValidationError('User is not found on this server')
        user.password = make_password(password)
        return user

    # def is_valid(self):
    #     return super().is_valid() and self.clean()

    class Meta:
        model = User
        fields = ('password',)


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        exclude = ('user', 'status')
