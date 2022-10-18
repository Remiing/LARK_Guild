from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from .models import Member
from .models import History


def index(request):
    # character_list = Member.objects.order_by('-character_item_level')
    # character_list = Member.objects.extra(select={'character_item_level_int': 'CAST(character_item_level AS INTEGER)'}).order_by('-character_item_level_int')
    context = {}
    return render(request, 'guild/index.html', context)


def chart(request):
    character_list = Member.objects.order_by('-character_item_level')
    character_history = {}
    for character in character_list:
        character_name = character.character_name
        last_update = character.modified_date.date()
        character_history[character_name] = History.objects.filter(character_name=character_name, date__gte=last_update)
    context = {'character_list': character_list, 'character_history': character_history}
    return render(request, 'guild/character_list.html', context)


def history(request, character_name):
    character_history = History.objects.filter(character_name=character_name).order_by('-date')
    context = {'character_name': character_name, 'character_history': character_history}
    return render(request, 'guild/character_history.html', context)

