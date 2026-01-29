from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from blog.models import Post
from .models import Comment


class CommentModelTests(TestCase):
    def test_comment_string_uses_user(self):
        user = get_user_model().objects.create_user(
            email="commenter@example.com",
            password="password123",
        )
        post = Post.objects.create(
            title="Post title",
            publish=timezone.now().date(),
        )
        comment = Comment.objects.create(user=user, post=post, content="Nice post!")
        self.assertEqual(str(comment), "commenter@example.com")

# Create your tests here.
