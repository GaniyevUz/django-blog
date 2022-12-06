from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView

from apps.forms import CustomLoginForm, RegisterForm, CreatePostForm, UserForm
from apps.models import Category, Post, Comment, User
from apps.utils.token import account_activation_token
from apps.utils.verify_email import send_verification


class AuthorPostListView(LoginRequiredMixin, ListView):
    template_name = 'apps/blog-category.html'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        slug = self.request.GET.get('category')
        author = self.request.user
        qs = self.get_queryset()
        context['posts'] = qs
        context['url'] = reverse('preview_author_posts')
        context['category'] = Category.objects.filter(slug=slug).first()
        return context

    def get_queryset(self, *args, **kwargs):
        author = self.request.user
        qs = Post.objects.order_by('-created_at').filter(author=author)
        if category := self.request.GET.get('category'):
            return qs.filter(category__slug=category, author=author)
        return qs


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'apps/auth/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('index')


class RegisterView(FormView):
    template_name = 'apps/auth/register.html'
    form_class = RegisterForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            send_verification(self.request, user)
            return render(self.request, 'apps/auth/temp.html',
                          {'title': 'Account activation', 'context': 'Check your email'})
        return super().form_valid(form)

    def form_invalid(self, form):
        context = {
            'forms': form
        }
        return render(self.request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('login')
        return super().get(request, *args, **kwargs)


class ProfileView(UpdateView):
    template_name = 'apps/auth/profile.html'
    form_class = UserForm
    success_url = reverse_lazy('profile')

    # queryset = User.objects.first()
    # if form.cleaned_data.get('avatar') is None:
    #     del form.cleaned_data['avatar']
    # User.objects.filter(pk=self.request.user.pk).update(**form.cleaned_data)

    # def dispatch(self, request, *args, **kwargs):
    #     options = {
    #         # 'page-size': 'Letter',
    #         'encoding': "UTF-8",
    #         # 'no-outline': None
    #     }
    #     # pdfkit.from_url('http://localhost:8000' + reverse('category'), 'out.pdf', options=options)
    #     return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        user = User.objects.get(pk=self.request.user.pk)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=user, form=form)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        return self.request.user


def ActivateAccountView(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    return render(request, 'apps/404.html')


def entry_not_found(request, exception, template_name='404.html'):
    return render(request, template_name)


class CreatePostView(LoginRequiredMixin, CreateView):
    form_class = CreatePostForm
    template_name = 'apps/add-post.html'
    success_url = reverse_lazy('category')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.author = self.request.user
        obj.title = form.data.get('title')
        category = form.data.get('category')
        post = obj.save()
        instance = Category.objects.create(post=post)

        instance.category.set(category)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


class PreviewDetailFormPostView(LoginRequiredMixin, DetailView):
    template_name = 'apps/post.html'
    queryset = Post.objects.all()
    context_object_name = 'post'

    # def dispatch(self, request, *args, **kwargs):
    #     user = request.user
    #     if user.is_superuser or user.is_staff:
    #         return super().dispatch(request, *args, **kwargs)
    #
    #     return render(request, 'apps/404.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_categories'] = Category.objects.filter(post=context.get('post'))
        context['comments'] = Comment.objects.filter(post__slug=self.request.path.split('/')[-1])
        return context
