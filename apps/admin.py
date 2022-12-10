from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.http import HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import reverse, path
from django.utils.html import format_html

from apps.models import Category, Post, About, Comment, User


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'post_count')
    exclude = ('slug',)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    search_fields = ('category__name', 'title')
    list_display = ('title', 'categories', 'status_icon', 'post_pic', 'created_at', 'status_button')
    exclude = ('slug',)
    list_filter = ('category', 'status', 'created_at')

    def status_icon(self, obj):
        data = {
            'pending': '<i class="fas fa-spinner fa-pulse" style="color: orange; font-size: 1.5em;"></i>',
            'active': '<i class="fa-solid fa-check" style="color: green; font-size: 1.5em;"></i>',
            'cancel': '<i class="fa-solid fa-circle-xmark"  style="color: red; font-size: 1.5em;"></i>'
        }
        return format_html(data[obj.status])

    def get_urls(self):
        urls = super().get_urls()
        my_url = [
            path('active/<int:id>', self.active),
            path('canceled/<int:id>', self.canceled),
        ]
        return urls + my_url

    def active(self, request, id):
        post = Post.objects.filter(id=id).first()
        post.status = 'active'
        post.save()
        return HttpResponseRedirect('../')

    def canceled(self, request, id):
        post = Post.objects.filter(id=id).first()
        post.status = 'cancel'
        post.save()
        return HttpResponseRedirect('../')

    def response_change(self, request, obj):
        if request.POST.get('view'):
            return redirect('post_form_detail', obj.slug)
        elif request.POST.get('status') and request.POST.get('status') in ['active', 'cancel']:
            obj.status = request.POST.get('status').lower()
            obj.save()
        return HttpResponseRedirect("./")

    def categories(self, obj: Post):  # NOQA
        lst = []
        for i in obj.category.all():
            lst.append(f'''<a href="{reverse('admin:apps_category_change', args=(i.pk,))}">{i.name}</a>''')
        return format_html(', '.join(lst))

    def post_pic(self, obj: Post):  # NOQA
        return format_html(f'<img style="border-radius: 5px;" width="70px" height="30px" src="{obj.pic.url}"/>')

    status_icon.short_description = 'status'


@admin.register(About)
class AboutAdmin(ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('comment', 'author', 'post')

    def comment(self, obj):
        return obj.text[:50] + '...'


@admin.register(User)
class UserAdmin(ModelAdmin):
    pass
