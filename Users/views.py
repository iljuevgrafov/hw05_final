from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm

# Create your views here.


def year(request):
    currentYear = dt.datetime.now().year
    return {'year': currentYear}


class SignUp(CreateView):
    def post(self, request):
        print(request.POST)
    form_class = CreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"
