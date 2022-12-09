from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, FormView

from apps.forms import CreateCommentForm
from apps.models import Category, Post, About, Comment, Contact


class IndexView(ListView):
    queryset = Category.objects.all()
    context_object_name = 'categories'
    template_name = 'apps/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['post'] = Post.objects.order_by('-created_at').first()
        context['url'] = reverse('category')
        context['posts'] = Post.objects.order_by('-created_at')[1:5]
        return context


class PostListView(ListView):
    queryset = Post.objects.filter(status__iexact='active').order_by('-created_at')
    template_name = 'apps/blog-category.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        slug = self.request.GET.get('category')
        context['url'] = reverse('category')
        context['category'] = Category.objects.filter(slug=slug).first()
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset()
        if category := self.request.GET.get('category'):
            return qs.filter(category__slug=category)
        return qs


class AboutView(ListView):
    # queryset = About.objects.first()
    template_name = 'apps/about.html'
    context_object_name = 'about'

    def get_queryset(self):
        return About.objects.first()


class ContactView(ListView):
    # template_name = 'apps/contact.html'
    template_name = 'apps/auth/temp.html'
    model = Contact
    fields = '__all__'
    context_object_name = 'contact'


class DetailFormPostView(FormView, DetailView):
    template_name = 'apps/post.html'
    queryset = Post.objects.all()
    context_object_name = 'post'
    form_class = CreateCommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_categories'] = Category.objects.filter(post=context.get('post'))
        context['comments'] = Comment.objects.filter(post__slug=self.request.path.split('/')[-1])
        return context

    def post(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        if 'comment' in request.POST:
            post = get_object_or_404(Post, slug=slug)
            data = {
                'post': post,
                'author': request.user,
                'text': request.POST.get('message'),
            }
            # form = self.form_class(data)
            form = Comment.objects.create(**data)
            form.save()
        return redirect('post_form_detail', slug)
