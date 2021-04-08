""" tests incoming activities"""
from unittest.mock import patch

from django.test import TestCase

from bookwyrm import models, views


# pylint: disable=too-many-public-methods
class InboxRemove(TestCase):
    """ inbox tests """

    def setUp(self):
        """ basic user and book data """
        self.local_user = models.User.objects.create_user(
            "mouse@example.com",
            "mouse@mouse.com",
            "mouseword",
            local=True,
            localname="mouse",
        )
        self.local_user.remote_id = "https://example.com/user/mouse"
        self.local_user.save(broadcast=False)
        with patch("bookwyrm.models.user.set_remote_server.delay"):
            self.remote_user = models.User.objects.create_user(
                "rat",
                "rat@rat.com",
                "ratword",
                local=False,
                remote_id="https://example.com/users/rat",
                inbox="https://example.com/users/rat/inbox",
                outbox="https://example.com/users/rat/outbox",
            )
        self.work = models.Work.objects.create(title="work title")
        self.book = models.Edition.objects.create(
            title="Test",
            remote_id="https://bookwyrm.social/book/37292",
            parent_work=self.work,
        )

        models.SiteSettings.objects.create()

    def test_handle_unshelve_book(self):
        """ remove a book from a shelf """
        shelf = models.Shelf.objects.create(user=self.remote_user, name="Test Shelf")
        shelf.remote_id = "https://bookwyrm.social/user/mouse/shelf/to-read"
        shelf.save()

        shelfbook = models.ShelfBook.objects.create(
            user=self.remote_user, shelf=shelf, book=self.book
        )

        self.assertEqual(shelf.books.first(), self.book)
        self.assertEqual(shelf.books.count(), 1)

        activity = {
            "id": shelfbook.remote_id,
            "type": "Remove",
            "actor": "https://example.com/users/rat",
            "object": {
                "type": "Edition",
                "title": "Test Title",
                "work": self.work.remote_id,
                "id": "https//bookwyrm.social/book/37292",
            },
            "target": "https://bookwyrm.social/user/mouse/shelf/to-read",
            "@context": "https://www.w3.org/ns/activitystreams",
        }
        views.inbox.activity_task(activity)
        self.assertFalse(shelf.books.exists())

    def test_handle_remove_book_from_list(self):
        """ listing a book """
        with patch("bookwyrm.models.activitypub_mixin.broadcast_task.delay"):
            booklist = models.List.objects.create(
                name="test list",
                user=self.local_user,
            )
            listitem = models.ListItem.objects.create(
                user=self.local_user,
                book=self.book,
                book_list=booklist,
            )
        self.assertEqual(booklist.books.count(), 1)

        activity = {
            "id": listitem.remote_id,
            "type": "Remove",
            "actor": "https://example.com/users/rat",
            "object": {
                "type": "Edition",
                "title": "Test Title",
                "work": self.work.remote_id,
                "id": "https://bookwyrm.social/book/37292",
            },
            "target": booklist.remote_id,
            "@context": "https://www.w3.org/ns/activitystreams",
        }
        views.inbox.activity_task(activity)

        self.assertEqual(booklist.books.count(), 0)
