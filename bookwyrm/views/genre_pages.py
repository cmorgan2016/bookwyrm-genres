from gc import get_objects
from django.contrib.postgres.search import TrigramSimilarity

from django.shortcuts import get_object_or_404, render

from bookwyrm.models.book import Genre, Book
from bookwyrm.forms import GenreForm

from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models.functions import Greatest
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.views import View
from django.views.generic import (
    DetailView,
    ListView,
)

class GenreDetailView(DetailView):
    template_name = 'genre/genre_detail_page.html'
    model = Genre

    def post(self, request, *args, **kwargs):
        '''Get the genres the user has selected.'''

        #buttonSelection = request.POST.get("search_buttons")
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['demo_books'] = Book.objects.filter(genres = self.get_object())[:4]
        return context