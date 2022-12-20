from time import time

from allauth.account.views import account_inactive
from faker import Faker
from django.core.management import BaseCommand

from apps.models import Post


class Command(BaseCommand):
    def handle(self, *args, **options):
        fake = Faker()
        start_time = time()
        for i in range(1, 20):
            Post.objects.create(
                title=fake.text(100),
                content=fake.sentence(1000),
                # author_id=fake.random.randint(1, 2),
                author_id=1,
                status=fake.random.choice([Post.Status.ACTIVE, Post.Status.PENDING])
            )
            print(f'post {i} has been created')
        end_time = time()
        print('Finished!!!')
        milliseconds = end_time - start_time
        print(f'Time elapsed: {milliseconds} milliseconds')