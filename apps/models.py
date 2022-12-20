from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db.models import ImageField, TextField, JSONField, Model, ForeignKey, DateTimeField, CharField, EmailField, \
    SlugField, CASCADE, SET_NULL, ManyToManyField, TextChoices, BooleanField, DateField, BigIntegerField, Manager, \
    PROTECT
from django.utils.html import format_html
from django.utils.text import slugify
from django_resized import ResizedImageField


class User(AbstractUser):
    avatar = ImageField(upload_to='authors/', null=True, blank=True)
    bio = TextField(null=True, blank=True)
    # social_accounts = JSONField(null=True, blank=True)
    email = EmailField(max_length=255, unique=True)
    is_active = BooleanField(default=False)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = CharField(validators=[phone_regex], max_length=17, null=True, blank=True)

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name


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
    author = ForeignKey(User, SET_NULL, null=True, blank=True)
    pic = ResizedImageField(upload_to='posts/', default='default-banner.jpg')
    category = ManyToManyField(Category)
    created_at = DateTimeField(auto_now_add=True)
    views = BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        # if not self.slug:
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


class Comment(Model):
    text = TextField()
    post = ForeignKey(Post, CASCADE)
    author = ForeignKey(User, CASCADE)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return format_html(f'<i>{self.text[:50]}... by {self.author.get_username()}</i>')


class Contact(Model):
    user = ForeignKey(User, PROTECT)
    subject = CharField(max_length=100)
    text = TextField()
    status = BooleanField(default=False, verbose_name='is answered')

    def __str__(self):
        return self.subject


class PostViewHistory(Model):
    post = ForeignKey(Post, CASCADE)
    viewed_at = DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.post.title} at {self.viewed_at}'
