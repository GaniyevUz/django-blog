from django.db.models import Count

from apps.models import Category, Post, About


def context_category(request):
    return {
        'categories': Category.objects.annotate(p_count=Count('post')).order_by('-p_count')[:2],
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
        # 'trending_post': Post.objects.extra(select={'created_at': 'MONTH(created_at)'}, order_by=['-created_at'])[:5]
        'trending_post': Post.objects.extra(order_by=['-created_at'])[:5]
    }
