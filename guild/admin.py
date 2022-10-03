from django.contrib import admin
from .models import Member
from .models import History


class MemberAdmin(admin.ModelAdmin):
    search_fields = ['character_name']
    list_display = ['character_name', 'character_class', 'character_item_level']


class HistoryAdmin(admin.ModelAdmin):
    search_fields = ['character_name']
    list_display = ['character_name', 'field', 'before_data', 'after_data', 'date']



admin.site.register(Member, MemberAdmin)
admin.site.register(History, HistoryAdmin)
