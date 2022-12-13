from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import ListView, DetailView, FormView

from apps.forms import CreateCommentForm, ContactForm
from apps.models import Post, About, Comment, PostViewHistory


class IndexView(ListView):
    queryset = Post.objects.order_by('-created_at').first()
    context_object_name = 'main_post'
    template_name = 'apps/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['url'] = reverse('category')
        context['posts'] = Post.objects.order_by('-created_at')[1:5]
        return context


class PostListView(ListView):
    queryset = Post.objects.filter(status__iexact=Post.Status.ACTIVE).order_by('-created_at')
    template_name = 'apps/blog-category.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['url'] = reverse('category')
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset()
        if category := self.request.GET.get('category'):
            return qs.filter(category__slug=category)
        return qs


class AboutView(ListView):
    template_name = 'apps/about.html'
    context_object_name = 'about'

    def get_queryset(self):
        return About.objects.first()


class ContactView(FormView):
    template_name = 'apps/contact.html'
    form_class = ContactForm

    def form_valid(self, form):
        if self.request.user.is_anonymous:
            return render(self.request, self.template_name, {'type': 'auth_error'})
        form.instance.user = self.request.user
        form.save()
        return render(self.request, self.template_name, {'type': 'success'})

    def form_invalid(self, form):
        return super().form_invalid(form)

    def get_success_url(self):
        return redirect('contact')


class DetailFormPostView(FormView, DetailView):
    template_name = 'apps/post.html'
    queryset = Post.objects.all()
    context_object_name = 'post'
    form_class = CreateCommentForm

    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        post = get_object_or_404(Post, slug=slug)
        if post:
            post.update_views()
            PostViewHistory.objects.create(post=post).save()
        return super().get(request, *args, **kwargs)

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
            comment = Comment.objects.create(**data)
            comment.save()
        return redirect('post_form_detail', slug)


def entry_not_found(request, exception, template_name='404.html'):
    return render(request, template_name)
