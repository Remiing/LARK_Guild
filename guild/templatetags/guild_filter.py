from django import template
import re

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


