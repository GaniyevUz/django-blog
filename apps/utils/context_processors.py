from datetime import date

from django.db.models import Count

from apps.models import Category, Post, About, PostViewHistory


def context_category(request):
    return {
        'categories': Category.objects.annotate(p_count=Count('post')).order_by('-p_count'),
        'tags': Category.objects.annotate(p_count=Count('post')).order_by('-p_count')
    }


def context_about(request):
    return {
        'about': About.objects.first()
    }


def context_post(request):
    return {
        'posts': Post.objects.all(),
        'feature_posts': Post.objects.order_by('-created_at')[:3],
        'trending_post': Post.objects.all()[:5]
        # 'trending_post': PostViewHistory.objects.filter(viewed_at__month__gt=date.today().month - 1)
    }
