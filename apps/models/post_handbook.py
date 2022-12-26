from django.core.validators import RegexValidator
from django.db.models import ImageField, TextField, JSONField, Model, ForeignKey, DateTimeField, CharField, EmailField, \
    SlugField, CASCADE, BooleanField, DateField, PROTECT
from django.utils.html import format_html
from django.utils.text import slugify

from apps.models import Post


class About(Model):
    image = ImageField(upload_to='')
    about = TextField()
    location = CharField(max_length=255)
    email = EmailField(max_length=255)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = CharField(validators=[phone_regex], max_length=17, blank=True)
    social_accounts = JSONField(null=True, blank=True)

    class Meta:
        verbose_name = 'Site Info'
        verbose_name_plural = 'Site Info'

    def __str__(self):
        return format_html(f'<i>{self.about[:50]}</i>')


class Category(Model):
    name = CharField(max_length=255)
    image = ImageField(upload_to='category/', default='category.png')
    slug = SlugField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # NOQA
            while Post.objects.filter(slug=self.slug).exists():
                slug = Post.objects.filter(slug=self.slug).first().slug
                if '-' in slug:
                    try:
                        if slug.split('-')[-1] in self.name:
                            self.slug += '-1'
                        else:
                            self.slug = '-'.join(slug.split('-')[:-1]) + '-' + str(int(slug.split('-')[-1]) + 1)
                    except:
                        self.slug = slug + '-1'
                else:
                    self.slug += '-1'
            super().save(*args, **kwargs)

    @property
    def post_count(self):
        return self.post_set.count()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Comment(Model):
    text = TextField()
    post = ForeignKey('apps.Post', CASCADE)
    author = ForeignKey('apps.User', CASCADE)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return format_html(f'<i>{self.text[:50]}... by {self.author.get_username()}</i>')


class Contact(Model):
    user = ForeignKey('apps.User', PROTECT)
    subject = CharField(max_length=100)
    text = TextField()
    status = BooleanField(default=False, verbose_name='is answered')

    def __str__(self):
        return self.subject


class PostViewHistory(Model):
    post = ForeignKey('apps.Post', CASCADE)
    viewed_at = DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.post.title} at {self.viewed_at}'
