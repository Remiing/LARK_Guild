import requests
from bs4 import BeautifulSoup
import re
import json
import selenium
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()
from guild.models import Member
from guild.models import History

def get_member_data(character_name):
    url = 'https://lostark.game.onstove.com/Profile/Character/'
    response = requests.get(url + character_name)
    soup = BeautifulSoup(response.text, 'html.parser')
    profile = soup.select_one('div.profile-ingame')
    if profile.select_one('div.profile-attention'):
        print(f'{character_name} 캐럭터 정보가 없습니다')
        return

    character_class = profile.select_one('div.profile-equipment__character > img')['alt']

    character_item_level = profile.select('div.level-info2__expedition > span')[1].text.replace('Lv.', '').replace(',', '')

    character_battle_level = profile.select('div.level-info__item > span')[1].text.replace('Lv.', '')

    character_expedition_level = profile.select('div.level-info__expedition > span')[1].text.replace('Lv.', '')

    character_engraving = [engraving.text for engraving in profile.select('div.profile-ability-engrave > div > div > ul > li > span')]
    character_engraving = ','.join(character_engraving)

    character_stat = [stat.text for stat in profile.select('div.profile-ability-battle > ul > li > span')]
    character_stat = [f'{character_stat[i]} {character_stat[i+1]}' for i in range(0, len(character_stat), 2) if character_stat[i] in ['치명', '특화', '신속']]
    character_stat = ','.join(character_stat)

    character_card = profile.select('div.profile-card__text > div > ul > li > div.card-effect__title')[-1].text

    character_gem = re.findall(r"\d{,2}레벨 ..의 보석", response.text)
    character_gem = sorted(character_gem, key=lambda x: (-int(re.search(r'\d+', x).group()), x.split()[1]))
    character_gem = ','.join(character_gem)

    character_equipment_level = re.findall(r"\+.+(?=</FONT></P>)", response.text)
    character_equipment_level = ','.join(character_equipment_level).replace('+', '')

    character_power = profile.select_one('div.profile-ability-basic > ul > li:nth-child(1) > span:nth-child(2)').text

    character_vitality = profile.select_one('div.profile-ability-basic > ul > li:nth-child(2) > span:nth-child(2)').text

    # print(character_gem)


    character_data = {
        'character_name': character_name,
        'character_class': character_class,
        'character_item_level': float(character_item_level),
        'character_battle_level': int(character_battle_level),
        'character_expedition_level': int(character_expedition_level),
        'character_engraving': character_engraving,
        'character_stat': character_stat,
        'character_card': character_card,
        'character_gem': character_gem,
        'character_equipment_level': character_equipment_level,
        'character_power': int(character_power),
        'character_vitality': int(character_vitality)
    }

    return character_data


def character_data_compare(character_data):
    character_name = character_data['character_name']
    member_obj = Member.objects.filter(character_name=character_name).first()
    change_check = 0
    if member_obj.character_item_level < character_data['character_item_level']:
        member_obj.character_item_level = character_data['character_item_level']
        History(character_name=character_name, field='character_item_level', before_data=member_obj.character_item_level, after_date=character_data['character_item_level']).save()
        change_check = 1
    if member_obj.character_battle_level < character_data['character_battle_level']:
        member_obj.character_battle_level = character_data['character_battle_level']
        History(character_name=character_name, field='character_battle_level', before_data=member_obj.character_battle_level, after_date=character_data['character_battle_level']).save()
        change_check = 1
    if member_obj.character_expedition_level < character_data['character_expedition_level']:
        member_obj.character_expedition_level = character_data['character_expedition_level']
        History(character_name=character_name, field='character_expedition_level', before_data=member_obj.character_expedition_level, after_date=character_data['character_expedition_level']).save()
        change_check = 1

    engraving_exist = sum(map(int, re.sub(r'[^0-9]', '', member_obj.character_engraving)))
    engraving_new = sum(map(int, re.sub(r'[^0-9]', '', character_data['character_engraving'])))
    if '원한' in character_data['character_engraving'] and engraving_exist < engraving_new:
        member_obj.character_engraving = character_data['character_engraving']
        History(character_name=character_name, field='character_engraving', before_data=member_obj.character_engraving, after_date=character_data['character_engraving']).save()
        change_check = 1

    stat_exist_sum = sum(map(int, member_obj.character_stat.replace('치명').replace('특화').replace('신속').split(',')))
    stat_new_sum = sum(map(int, character_data['character_stat'].replace('치명').replace('특화').replace('신속').split(',')))
    if stat_exist_sum < stat_new_sum:
        member_obj.character_stat = character_data['character_stat']
        History(character_name=character_name, field='character_stat', before_data=member_obj.character_stat, after_date=character_data['character_stat']).save()
        change_check = 1

    card_dealer = ['', '남겨진 바람의 절벽 6세트 (12각성합계)', '카제로스의 군단장 6세트 (12각성합계)', '세상을 구하는 빛 6세트 (18각성합계)', '카제로스의 군단장 6세트 (18각성합계)', '세상을 구하는 빛 6세트 (30각성합계)']
    card_supporter = ['', '남겨진 바람의 절벽 6세트 (30각성합계)']
    card_list = card_supporter if member_obj.character_class in ['바드', '홀리나이트', '도화가'] else card_dealer
    card_exist = card_list.index(member_obj.character_card) if member_obj.character_card in card_list else 0
    card_new = card_list.index(character_data['character_card']) if character_data['character_card'] in card_list else 0
    if card_exist < card_new:
        member_obj.character_card = character_data['character_card']
        History(character_name=character_name, field='character_card', before_data=member_obj.character_card, after_date=character_data['character_card']).save()
        change_check = 1

    gem_exist = member_obj.character_gem.split(',')
    gem_new = character_data['character_gem'].split(',')
    for gem in gem_exist[:]:
        if gem in gem_new:
            gem_exist.remove(gem)
            gem_new.remove(gem)
    if gem_new:
        member_obj.character_gem = character_data['character_gem']
        change_check = 1

    equipment_exist = map(int, [value.split(' ')[0] for value in member_obj.character_equipment_level.split(',')])
    equipment_new = map(int, [value.split(' ')[0] for value in character_data['character_equipment_level'].split(',')])
    for equip1, equip2 in zip(equipment_exist, equipment_new):
        if equip1!=equip2:

    if member_obj.character_equipment_level != character_data['character_equipment_level']:
        member_obj.character_equipment_level = character_data['character_equipment_level']
        change_check = 1
    if member_obj.character_power < character_data['character_power']:
        member_obj.character_power = character_data['character_power']
        change_check = 1
    if member_obj.character_vitality < character_data['character_vitality']:
        member_obj.character_vitality = character_data['character_vitality']
        change_check = 1

    if change_check:
        member_obj.save()


def add_data(character_data):
    member_obj = Member.objects.filter(character_name=character_data['character_name']).first()
    if not member_obj:
        member_obj = Member()
    member_obj.character_name = character_data['character_name']
    member_obj.character_class = character_data['character_class']
    member_obj.character_item_level = character_data['character_item_level']
    member_obj.character_battle_level = character_data['character_battle_level']
    member_obj.character_expedition_level = character_data['character_expedition_level']
    member_obj.character_engraving = character_data['character_engraving']
    member_obj.character_stat = character_data['character_stat']
    member_obj.character_card = character_data['character_card']
    member_obj.character_gem = character_data['character_gem']
    member_obj.character_equipment_level = character_data['character_equipment_level']
    member_obj.character_power = character_data['character_power']
    member_obj.character_vitality = character_data['character_vitality']
    member_obj.save()


def test(character_name):
    member_obj = Member.objects.filter(character_name=character_name).first()
    print(member_obj.__dict__)



if __name__ == '__main__':
    guild_memeber = ['너와떠나는여행', '채연', '유혈랑', '우유맛조아', '데이지아SR', '남순이견주', '묵련비', '피망꼬치구이', '강배', '명하누', '킹기다킹기', '배천덕', '송저송', '블루밍소설', '신레델라', '그거저아닌데', '배낼', '헵짚', '야레기', '능동로무법자', '메리크리스마스', '커피바드세요', '능동로솜주먹', '퍄닥퍄닥퍄닥퍄닥', '귀여운눈나', 'S순이견주2', '보이드어벤저', '잠옷소년', '추합', '썬연료2', '왜이리더워', '붕슼', '그리워아만', '훈건창', '파이터팽', '꿈꾸세요', '시린미', '대근짱짱', '돈룡', '징징EYA']
    for member in guild_memeber:
        character_data = get_member_data(member)
        if not character_data:continue
        add_data(character_data)
        print(f'{member} data saved')

    # test('너와떠나는여행')

    # character_name = '너와떠나는여행'
    # character_data = get_member_data(character_name)

