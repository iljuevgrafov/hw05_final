from django.test import TestCase, Client
import datetime as dt
from django.contrib.auth import get_user_model


class YatubeTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.client = Client()

    # def test_user_reg(self):
    #     response = self.client.post('/auth/signup', {'first_name': ['Name'], 'last_name': ['Surname'], 'username': [
    #                                 'testuser'], 'email': ['test@yandex.ru'], 'password1': ['Zz000000'], 'password2': ['Zz000000']}, follow=True)

   def test_login(self):
        self.user = self.User.objects.create_user(
            username="john", email="john@mail.com", password="12345")
        # response = self.client.post(
        #     '/auth/login/?next=&username=leo&password=Zz000000')
        response = self.client.post(
            '/auth/login', {'username': 'leo', 'password': 'Zaq123ws'}, follow=True)
        # response = self.client.post('/auth/signup', {'first_name': 'Name', 'last_name': 'Surname', 'username':
        #                                              'testuser', 'email': 'test@yyy.ru', 'password1': 'Zz000000', 'password2': 'Zz000000'}, follow=True)
        for template in response.templates:
            print(template.name)
        # print(self.User.objects.get(username='john'))

    def test_new_post_auth(self):
        pass

    def test_new_post_no_auth(self):
        pass

    def test_new_post_os_pages(self):
        pass

    def test_post_edit(self):
        pass

