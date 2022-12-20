from django.views import View
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, TemplateView
from apps.forms import CustomLoginForm, RegisterForm, CreatePostForm, UserForm, ChangePasswordForm, ResetPasswordForm

from apps.models import Category, Post, Comment, User
from apps.utils import send_to_gmail, one_time_token
from apps.utils.sms import send, check


class AccountSettingMixin(View):
    def check_one_time_link(self, data):
        uid64 = data.get('uid64')
        token = data.get('token')
        try:
            uid = force_str(urlsafe_base64_decode(uid64))
            user = User.objects.get(pk=uid)
        except Exception as e:
            print(e)
            user = None
        if user is not None and one_time_token.check_token(user, token):
            user.is_active = True
            user.save()
            return user
        return False


class AuthorPostListView(LoginRequiredMixin, ListView):
    template_name = 'apps/blog-category.html'
    queryset = Post.objects.order_by('-created_at')
    context_object_name = 'posts'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        context['url'] = reverse('preview_author_posts')
        context['owner_post'] = True
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        author = self.request.user
        qs = qs.filter(author=author)
        if category := self.request.GET.get('category'):
            return qs.filter(category__slug=category)
        return qs


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'apps/auth/login.html'
    fields = '__all__'
    redirect_authenticated_user = True
    next_page = reverse_lazy('index')


class RegisterView(FormView):
    template_name = 'apps/auth/register.html'
    form_class = RegisterForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        if user:
            current_site = get_current_site(self.request)
            send_to_gmail.apply_async(
                args=[form.data.get('email'), current_site.domain],
                countdown=5
            )
            return render(self.request, 'apps/auth/register.html', {'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=self.form_class)
        return render(self.request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('login')
        return super().get(request, *args, **kwargs)


class ChangePasswordView(LoginRequiredMixin, UpdateView):
    form_class = ChangePasswordForm
    success_url = reverse_lazy('index')
    template_name = 'apps/auth/change-password.html'
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        username = self.request.user.username
        valid_form = super().form_valid(form)
        password = form.data.get('new_password')
        user = authenticate(username=username, password=password)
        if user:
            login(self.request, user)
        return valid_form

    def get_object(self, queryset=None):
        return self.request.user


class ResetPasswordView(AccountSettingMixin, UpdateView):
    template_name = 'apps/auth/reset-password.html'
    success_url = reverse_lazy('index')

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        if 'save_password' in request.POST:
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                form.save()
            return redirect('login')

        email = self.request.POST.get('email')
        current_site = get_current_site(self.request)
        if user := User.objects.get(email=email):
            user.is_active = False
            user.save()
            send_to_gmail.apply_async(
                args=[email, current_site.domain, 'reset'],
                countdown=5
            )
            return render(request, self.template_name, {'type': 'valid'})
        return super().post(self, request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.GET.get('uid64') and request.GET.get('token'):
            if user := self.check_one_time_link(request.GET):
                return render(request, self.template_name,
                              {'reset_password_user': urlsafe_base64_encode(force_bytes(str(user.pk)))})
            return render(request, self.template_name, {'type': 'expired'})
        return render(request, self.template_name)


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'apps/auth/profile.html'
    form_class = UserForm
    success_url = reverse_lazy('profile')
    login_url = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get(self, request, **kwargs):
        self.object = self.request.user
        context = self.get_context_data(object=self.object, form=self.form_class)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        return self.request.user


class ActivateEmailView(AccountSettingMixin, TemplateView):
    template_name = 'apps/auth/temp.html'

    def get(self, request, *args, **kwargs):
        if user := self.check_one_time_link(kwargs):
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('index')
        else:
            return HttpResponse('Activation link is invalid!')


class CreatePostView(LoginRequiredMixin, CreateView):
    form_class = CreatePostForm
    template_name = 'apps/add-post.html'
    success_url = reverse_lazy('preview_author_posts')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class PreviewDetailFormPostView(LoginRequiredMixin, DetailView):
    template_name = 'apps/post.html'
    queryset = Post.objects.all()
    context_object_name = 'post'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        return render(request, 'apps/404.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_categories'] = Category.objects.filter(post=context.get('post'))
        context['comments'] = Comment.objects.filter(post__slug=self.request.path.split('/')[-1])
        return context


class VerifySMSView(LoginRequiredMixin, TemplateView):
    template_name = 'apps/auth/change-password.html'
    login_url = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        phone = request.POST.get('phone')
        if request.POST.get('send'):
            send(phone)
            user = request.user
            user.phone = phone
            user.save()
            return render(request, self.template_name, {'verify': 'ok'})
        elif request.POST.get('verify'):
            code = request.POST.get('code')
            if check(request.user.phone, code):
                user = request.user
                user.is_staff = True
                user.save()
                return render(request, self.template_name, {'verify': 'no', 'type': 'yes'})
            return render(request, self.template_name, {'verify': 'no', 'type': 'no'})
        return render(request, self.template_name, {'verify': 'no'})


class DeleteAccountView(View):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.user.delete()
        return redirect('register')
