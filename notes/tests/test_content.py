from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


from notes.models import Note

User = get_user_model()


class TestContent(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    LIST_URL = 'notes:list'

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Писатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='newnote',
            author=cls.author)

    def test_notes_list_in_object_list(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        url = reverse(self.LIST_URL)
        response = self.client.get(url)
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_another_user(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.reader)
        url = reverse(self.LIST_URL)
        response = self.client.get(url)
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        self.client.force_login(self.author)
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
