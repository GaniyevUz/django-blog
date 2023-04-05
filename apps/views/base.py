import os

import qrcode
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, FormView, TemplateView

from apps.forms import CreateCommentForm, ContactForm
from apps.models import Post, About, Comment, PostViewHistory
from apps.utils.page2pdf import render_to_pdf


class SearchView(View):
    def post(self, request, *args, **kwargs):
        like = request.POST.get('like')
        data = {
            'posts': list(Post.objects.filter(title__icontains=like).values('title', 'pic', 'slug')[:5])
        }
        return JsonResponse(data)


class IndexView(ListView):
    queryset = Post.active.all()[:1]
    context_object_name = 'main_post'
    template_name = 'apps/index.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context['main_post'] = context['main_post'][0]
        context['url'] = reverse('category')
        context['posts'] = Post.active.all()[1:5]
        return context

    def get(self, request, *args, **kwargs):
        context = Post.active.exists()
        if not context:
            return redirect('create_post')
        return super().get(request, *args, **kwargs)


class PostListView(ListView):
    queryset = Post.active.all()
    template_name = 'apps/blog-category.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        pagination = context['page_obj']
        paginator = pagination.paginator
        page = pagination.number
        left = (int(page) - 4)
        if left < 1:
            left = 1
        right = (int(page) + 5)
        if right > paginator.num_pages:
            right = paginator.num_pages + 1
        context['pagination_range'] = range(left, right)
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


class GeneratePdf(DetailView):
    slug_url_kwarg = 'pk'

    def get(self, request, *args, **kwargs):
        post = Post.objects.get(pk=kwargs.get('pk'))
        img = qrcode.make(f'{get_current_site(request)}/post/{post.slug}')
        img.save(post.slug + '.png')
        data = {
            'post': post,
            'qrcode': f'{os.getcwd()}/{post.slug}.png'
        }
        pdf = render_to_pdf('page2pdf.html', data)
        return HttpResponse(pdf, content_type='application/pdf')


def entry_not_found(request, exception, template_name='404.html'):
    return render(request, template_name)


class InActiveView(TemplateView):
    template_name = 'apps/auth/inactive.html'
