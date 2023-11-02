from django.test import TestCase
from django.contrib.auth import get_user_model


User = get_user_model()


class UserModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        User.objects.create(username='Test User', first_name='Test', last_name='User', email='testuser@email.com')

    def test_username(self):
        user = User.objects.get(id=1)
        self.assertEqual(user.username, 'Test User')
    
    def test_email(self):
        user = User.objects.get(id=1)
        self.assertEqual(user.email, 'testuser@email.com')
    
    def test_first_name_max_length(self):
        user = User.objects.get(id=1)
        max_length = user._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 150)

    def test_object_name_is_user_name(self):
        user = User.objects.get(id=1)
        expected_object_name = user.username
        self.assertEqual(str(user), expected_object_name)
