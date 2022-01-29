from django.forms import ValidationError
from django.urls import path, include
from django.http import HttpResponse
from .models import Actor,FilmActor,Film
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django.shortcuts import render
def test(request):

    # Q1 Create a list of all the actors’ first name and last name. Display the first and last name of each actor in a single column in upper case letters. Name the column Actor Name.
    
    result = Actor.objects.annotate(
        name=Concat('first_name', Value(' '), 'last_name',
        output_field=CharField())
    ).values("name")







    for it in result:
        print(it)
    return render("superset/hello.html",)

urlpatterns = [
 path("",test)
]