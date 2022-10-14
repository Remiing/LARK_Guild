from django.db import models
import re
from datetime import datetime, timedelta


class Member(models.Model):
    character_name = models.CharField(max_length=12, primary_key=True)  #캐릭터명
    character_class = models.CharField(max_length=6)
    character_item_level = models.FloatField()
    character_battle_level = models.IntegerField()
    character_expedition_level = models.IntegerField()
    character_engraving = models.CharField(max_length=200)
    character_stat = models.CharField(max_length=200)
    character_card = models.CharField(max_length=50)
    character_gem = models.CharField(max_length=200)
    character_equipment_level = models.CharField(max_length=200)
    character_power = models.IntegerField()
    character_vitality = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True, editable=True)
    modified_date = models.DateTimeField(auto_now=True, editable=True)

    def stat_as_list(self):
        return [stat for stat in self.character_stat.split(',') if stat[:2] in ['치명', '특화', '신속']]

    def equipment_weapon_lv(self):
        return re.sub(r'[^0-9]', '', self.character_equipment_level.split(',')[0])

    def equipment_as_list(self):
        return self.character_equipment_level.split(',')

    def engraving_simple(self):
        return re.sub(r'[^0-9]', '', self.character_engraving)

    def engraving_as_list(self):
        return self.character_engraving.split(',')

    def card_slice(self):
        return self.character_card.replace(')', '').split(' (')

    def gem_simple(self):
        if not self.character_gem: return
        gem_list = self.character_gem.split(',')
        counter = {}
        for gem in gem_list:
            gem = gem.replace('의 보석', '')
            if gem in counter:
                counter[gem] += 1
            else:
                counter[gem] = 1
        return [f'{key} x{value}' for key, value in counter.items()]

    @property
    def elapsed_time(self):
        time = datetime.now() - self.modified_date
        if time < timedelta(days=1):
            return '오늘'
        elif time < timedelta(days=7):
            return f'{datetime.now().day - self.modified_date.day}일전'
        else:
            return f'{self.modified_date.month}.{self.modified_date.day}'

    def __str__(self):
        return self.character_name


class History(models.Model):
    character_name = models.ForeignKey(Member, on_delete=models.CASCADE)
    field = models.CharField(max_length=50)
    before_data = models.CharField(max_length=200)
    after_data = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)






