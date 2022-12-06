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
        context['posts'] = Post.objects.order_by('-created_at')[:4]
        return context


class PostListView(ListView):
    queryset = Post.objects.order_by('-created_at')
    template_name = 'apps/blog-category.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        slug = self.request.GET.get('category')
        # qs = self.get_queryset()
        # context['posts'] = qs
        context['url'] = reverse('category')
        context['category'] = Category.objects.filter(slug=slug).first()
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset()
        if category := self.request.GET.get('category'):
            return qs.filter(category__slug=category)
        return qs


class AboutView(ListView):
    queryset = About.objects.first()
    template_name = 'apps/about.html'
    context_object_name = 'about'

    def get_queryset(self):
        return super().get_queryset()


class ContactView(ListView):
    template_name = 'apps/contact.html'
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
        post = get_object_or_404(Post, slug=slug)
        data = {
            'post': post,
            'author': request.user,
            'text': request.POST.get('text'),
        }
        form = self.form_class(data)
        if form.is_valid():
            form.save()
        return redirect('post_form_detail', slug)


from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


# Opens up page as PDF
class ViewPDF(View):
    def get(self, request, *args, **kwargs):
        context = {'posts': Post.objects.all(), 'url': reverse('category'), 'category': Category.objects.all()}
        pdf = render_to_pdf('apps/blog-category.html', context)
        return HttpResponse(pdf, content_type='application/pdf')


# Automaticly downloads to PDF file
class DownloadPDF(View):
    def get(self, request, *args, **kwargs):
        context = {'url': reverse('category'), 'category': Category.objects.all()}
        pdf = render_to_pdf('apps/blog-category.html', context)

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "Invoice_%s.pdf" % ("12341231")
        content = "attachment; filename='%s'" % (filename)
        response['Content-Disposition'] = content
        return response
