from django.test import TestCase
from django.utils import timezone

from .models import Post


class BlogModelTests(TestCase):
    def test_post_slug_generated(self):
        post = Post.objects.create(
            title="Hello World",
            publish=timezone.now().date(),
        )
        self.assertTrue(post.slug)

# Create your tests here.
