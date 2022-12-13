from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.views import IndexView, AboutView, ContactView, PostListView, CustomLoginView, RegisterView, \
    DetailFormPostView, CreatePostView, PreviewDetailFormPostView, AuthorPostListView, ProfileView, ActivateEmailView, \
    ChangePasswordView, ResetPasswordView

urlpatterns = [
    path('login', CustomLoginView.as_view(), name='login'),
    path('register', RegisterView.as_view(), name='register'),
    path('logout', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('change-password', ChangePasswordView.as_view(), name='change_password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset_password'),

    path('about', AboutView.as_view(), name='about'),
    path('contact', ContactView.as_view(), name='contact'),
    path('blog-category', PostListView.as_view(), name='category'),
    path('post/<str:slug>', DetailFormPostView.as_view(), name='post_form_detail'),

    path('my-blogs', AuthorPostListView.as_view(), name='preview_author_posts'),
    path('preview-post/<str:slug>', PreviewDetailFormPostView.as_view(), name='preview_post_form_detail'),
    path('create-post', CreatePostView.as_view(), name='create_post'),

    path('activate/<str:uid64>/<str:token>', ActivateEmailView.as_view(), name='activate_user'),
    path('', IndexView.as_view(), name='index'),
]
