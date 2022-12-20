from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.html import format_html

from apps.models import Category, Post, About, Comment, User, Contact
from apps.utils import send_to_contact


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'post_count')
    exclude = ('slug',)


@admin.register(Post)
class PostAdmin(ModelAdmin):
    search_fields = ('category__name', 'title')
    list_display = (
        'post_title', 'categories', 'views', 'status_icon', 'post_pic', 'created_at', 'status_button', 'make_pdf')
    exclude = ('slug', 'views')
    list_filter = ('category', 'status', 'created_at')
    readonly_fields = ('status',)
    list_per_page = 10

    change_form_template = 'admin/custom/change_form_post.html'

    # list_editable = ('pic', )

    def status_icon(self, obj):
        data = {
            'pending': '''<script src="https://cdn.lordicon.com/fudrjiwc.js"></script><lord-icon src="https://cdn.lordicon.com/uutnmngi.json" trigger="hover" colors="primary:#4be1ec,secondary:#cb5eee" stroke="65" style="width:30px;height:30px"></lord-icon>''',
            # 'pending': '<i class="fas fa-spinner fa-pulse" style="color: orange; font-size: 1.5em;"></i>',
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
        post = Post.objects.get(id=id)
        post.status = Post.Status.ACTIVE
        post.save()
        return HttpResponseRedirect('../')

    def canceled(self, request, id):
        post = Post.objects.get(id=id)
        post.status = Post.Status.CANCEL
        post.save()
        return HttpResponseRedirect('../')

    def response_change(self, request, obj):
        if request.POST.get('view'):
            return redirect('preview_post_form_detail', obj.slug)
        elif request.POST.get('status') and request.POST.get('status') in [Post.Status.ACTIVE, Post.Status.CANCEL]:
            obj.status = request.POST.get('status')
            obj.save()
        return HttpResponseRedirect("./")

    def make_pdf(self, obj: Post):
        return format_html(f'<a href="/pdf/{obj.id}"><input type="button" style="background-color: #4bbda6;" value="Make PDF"></a>')

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

    # readonly_fields = ('post', 'author', 'text')

    def comment(self, obj):
        return obj.text[:50] + '...'


@admin.register(User)
class UserAdmin(ModelAdmin):
    pass


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    change_form_template = 'admin/custom/change_form_message.html'
    list_display = ('subject', 'user', 'status')
    exclude = ('status',)
    readonly_fields = ('user', 'subject', 'text')
    list_filter = ('status',)
    list_per_page = 15

    def has_change_permission(self, request, obj=None):
        return False

    def response_change(self, request, obj):
        if request.POST.get('send_mail'):
            obj.status = True
            obj.save()
            send_to_contact.apply_async(
                args=[obj.user.email],
                countdown=5
            )
            return HttpResponseRedirect('../')
