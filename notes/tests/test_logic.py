from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify

User = get_user_model()


class TestContent(TestCase):

    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'newslug'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Адрес страницы с заметкой.
        cls.url = reverse('notes:add')
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': cls.NOTE_SLUG
        }

    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_authorized_user_cant_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        self.auth_client.post(self.url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе 1 - сравниваем с 1.
        self.assertEqual(notes_count, 1)

    def test_not_unique_slug(self):
        # Совершаем запрос через авторизованный клиент.
        # Создаем первую заметку
        self.auth_client.post(self.url, data=self.form_data)
        # Создаем вторую заметку с таким же slug
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.NOTE_SLUG + '' + WARNING
        )
        # Дополнительно убедимся, что заметка не была создана.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе есть первый коментарий - сравниваем с 1.
        self.assertEqual(notes_count, 1)

    def test_empty_slug(self):
        # Убираем поле slug из словаря:
        self.form_data.pop('slug')
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе 1 - сравниваем с 1.
        self.assertEqual(notes_count, 1)
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)


class TestContentEditDelete(TestCase):

    NOTE_TEXT = 'Текст заметки'
    NOTE_SLUG = 'newslug'

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Писатель простой')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='newnote',
            author=cls.author)
        # Данные для POST-запроса при изменении заметки.
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': cls.NOTE_SLUG
        }

    def test_author_can_edit_note(self):
        # Получаем адрес страницы редактирования заметки:
        url = reverse('notes:edit', args=(self.note.slug,))
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.author_client.post(url, self.form_data)
        # Проверяем редирект:
        self.assertRedirects(response, reverse('notes:success'))
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        self.note.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        # Получаем адрес страницы редактирования заметки:
        url = reverse('notes:edit', args=(self.note.slug,))
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.reader_client.post(url, self.form_data)
        # Проверяем, что страница не найдена:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем новый объект запросом из БД.
        note_from_db = Note.objects.get(id=self.note.id)
        # Проверяем, что атрибуты объекта из БД
        # равны атрибутам заметки до запроса.
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.reader_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
