from ckeditor_uploader.fields import RichTextUploadingField
from django.db.models import Model, ForeignKey, DateTimeField, CharField, SlugField, SET_NULL, ManyToManyField, \
    TextChoices, \
    BigIntegerField, Manager
from django.utils.html import format_html
from django.utils.text import slugify
from django_resized import ResizedImageField


class ActivePostsManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.ACTIVE)


class Post(Model):
    class Status(TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        CANCEL = 'cancel', 'Cancel'

    title = CharField(max_length=255)
    slug = SlugField(max_length=255, unique=True)
    content = RichTextUploadingField()
    status = CharField(max_length=25, choices=Status.choices, default=Status.PENDING)
    author = ForeignKey('apps.User', SET_NULL, null=True, blank=True)
    pic = ResizedImageField(upload_to='posts/', default='default-banner.jpg')
    category = ManyToManyField('apps.Category')
    created_at = DateTimeField(auto_now_add=True)
    views = BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            while Post.objects.filter(slug=self.slug).exists():
                slug = Post.objects.filter(slug=self.slug).first().slug
                if '-' in slug:
                    try:
                        if slug.split('-')[-1] in self.title:
                            self.slug += '-1'
                        else:
                            self.slug = '-'.join(slug.split('-')[:-1]) + '-' + str(int(slug.split('-')[-1]) + 1)
                    except:
                        self.slug = slug + '-1'
                else:
                    self.slug += '-1'

        super().save(*args, **kwargs)

    def update_views(self, *args, **kwargs):
        self.views = self.views + 1
        super().save(*args, **kwargs)
        return self.views

    @property
    def comment_count(self):
        return self.comment_set.count()

    @property
    def post_title(self):
        return self.title[:50] + '...'

    def __str__(self):
        return self.title

    objects = Manager()
    active = ActivePostsManager()

    def status_button(self):
        if self.status == Post.Status.PENDING:
            return format_html(
                f'''<a href="active/{self.id}">
                        <input type="button" style="background-color: #96be5b;" value="Active">
                    </a>
                    <a href="canceled/{self.id}">
                        <input type="button" style="background-color: #de8652;" value="Cancel">
                    </a>'''
            )
        elif self.status == Post.Status.ACTIVE:
            return format_html(
                f'''<a style="color: green; font-size: 1.10em;margin-top: 8px; margin: auto;">Accepted</a>''')

        return format_html(
            f'''<a style="color: red; font-size: 1.10em;margin-top: 8px; margin: auto;">Canceled</a>''')

    class Meta:
        ordering = ['-created_at']
