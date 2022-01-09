from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаём запись в БД для проверки доступности адреса group/test-slug/
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
            slug='test-slug',
        )
        # создаём автора тестового поста
        cls.author = User.objects.create(username='Test_author')
        # создаём тестовый пост
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста для теста',
            group=cls.group
        )
        cls.pages_properties = {
            'index': {
                'url': '/',
                'template': 'posts/index.html'
            },
            'group_list': {
                'url': f'/group/{cls.group.slug}/',
                'template': 'posts/group_list.html',
            },
            'profile': {
                'url': f'/profile/{cls.author}/',
                'template': 'posts/profile.html'
            },
            'post_detail': {
                'url': f'/posts/{cls.post.id}/',
                'template': 'posts/post_detail.html'
            },
            'post_edit': {
                'url': f'/posts/{cls.post.id}/edit/',
                'template': 'posts/create_post.html'
            },
            'create_post': {
                'url': '/create/',
                'template': 'posts/create_post.html'
            },
        }

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create(username='NormalUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_templates(self):
        """Проверка использования правильных шаблонов для вызываемых страниц"""
        for page, page_properties in self.pages_properties.items():
            with self.subTest(page=page):
                response = self.authorized_author.get(page_properties['url'])
                template = page_properties['template']
                self.assertTemplateUsed(response, template)

    def test_unexistng_page(self):
        """Проверка запроса к несуществующей странице"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_access_to_pages_according_rights(self):
        """Проверка доступа к страницам согласно прав пользователей"""
        access_rights = {
            self.guest: ['index', 'group_list', 'profile', 'post_detail'],
            self.authorized_client: ['create_post'],
            self.authorized_author: ['post_edit']
        }
        for user, pages in access_rights.items():
            with self.subTest(user=user):
                for page in pages:
                    with self.subTest(page=page):
                        response = user.get(self.pages_properties[page]['url'])
                        self.assertEqual(response.status_code, HTTPStatus.OK)
