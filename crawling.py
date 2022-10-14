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
    # for key, value in member_obj.__dict__.items():
    #     print(key, '|', value)
    # print('-------------------------------------------')
    change_check = 0

    # 아이템 레벨
    field = 'character_item_level'
    before_data = member_obj.character_item_level
    after_data = character_data[field]
    if before_data < after_data:
        add_history(member_obj, field, before_data, after_data)
        member_obj.character_item_level = character_data[field]
        change_check = 1

    # 전투 레벨
    field = 'character_battle_level'
    before_data = member_obj.character_battle_level
    after_data = character_data[field]
    if before_data < after_data:
        add_history(member_obj, field, before_data, after_data)
        member_obj.character_battle_level = character_data[field]
        change_check = 1

    # 원정대 레벨
    field = 'character_expedition_level'
    before_data = member_obj.character_expedition_level
    after_data = character_data[field]
    if before_data < after_data:
        add_history(member_obj, field, before_data, after_data)
        member_obj.character_expedition_level = character_data[field]
        change_check = 1

    # 각인
    field = 'character_engraving'
    before_data = member_obj.character_engraving
    after_data = character_data[field]
    if before_data != after_data:
        engraving_exist_simple = sum(map(int, re.sub(r'[^0-9]', '', before_data)))
        engraving_new_simple = sum(map(int, re.sub(r'[^0-9]', '', after_data)))
        if '원한' in after_data and engraving_exist_simple < engraving_new_simple:
            add_history(member_obj, field, before_data, after_data)
            member_obj.character_engraving = character_data[field]
            change_check = 1

    # 특성
    field = 'character_stat'
    before_data = member_obj.character_stat
    after_data = character_data[field]
    if before_data != after_data:
        stat_exist = list(map(int, before_data.replace('치명', '').replace('특화', '').replace('신속', '').split(',')))
        stat_new = list(map(int, after_data.replace('치명', '').replace('특화', '').replace('신속', '').split(',')))
        stat_max = [65+1620+168, 60+620, 56]  # 특성 최댓값(내실치명+악세특성+펫효과, 특화+악세특성, 신속)
        if sum(stat_exist) < sum(stat_new) <= sum(stat_max) and max(stat_new) <= max(stat_max):
            add_history(member_obj, field, before_data, after_data)
            member_obj.character_stat = character_data[field]
            change_check = 1

    # 카드
    field = 'character_card'
    before_data = member_obj.character_card
    after_data = character_data[field]
    if before_data != after_data:
        card_dealer = ['', '남겨진 바람의 절벽 6세트 (12각성합계)', '카제로스의 군단장 6세트 (12각성합계)', '세상을 구하는 빛 6세트 (18각성합계)', '카제로스의 군단장 6세트 (18각성합계)', '세상을 구하는 빛 6세트 (30각성합계)']
        card_supporter = ['', '남겨진 바람의 절벽 6세트 (30각성합계)']
        card_list = card_supporter if member_obj.character_class in ['바드', '홀리나이트', '도화가'] else card_dealer
        card_exist_num = card_list.index(before_data) if before_data in card_list else 0
        card_new_num = card_list.index(after_data) if after_data in card_list else 0
        if card_exist_num < card_new_num:
            add_history(member_obj, field, before_data, after_data)
            member_obj.character_card = character_data[field]
            change_check = 1

    # 보석
    field = 'character_gem'
    before_data = member_obj.character_gem
    after_data = character_data[field]
    if before_data != after_data and not after_data:
        gem_exist_list = before_data.split(',')
        gem_new_list = after_data.split(',')
        for gem in gem_exist_list[:]:
            if gem in gem_new_list:
                gem_exist_list.remove(gem)
                gem_new_list.remove(gem)
        for gem_exist, gem_new in zip(gem_exist_list, gem_new_list):
            if int(re.search(r'\d+', gem_exist).group()) == int(re.search(r'\d+', gem_new).group()): continue
            add_history(member_obj, field, gem_exist, gem_new)
        member_obj.character_gem = character_data[field]
        change_check = 1

    # 장비 강화 단계
    field = 'character_equipment_level'
    before_data = member_obj.character_equipment_level
    after_data = character_data[field]
    if before_data != after_data:
        equipment_exist_list = before_data.split(',')
        equipment_new_list = after_data.split(',')
        equipment_exist_simple = list(map(int, [value.split(' ')[0] for value in before_data.split(',')]))
        equipment_new_simple = list(map(int, [value.split(' ')[0] for value in after_data.split(',')]))
        for i, (num_exist, num_new) in enumerate(zip(equipment_exist_simple, equipment_new_simple)):
            if num_exist < num_new:
                add_history(member_obj, field, equipment_exist_list[i], equipment_new_list[i])
        member_obj.character_equipment_level = character_data[field]

    # 공격력
    field = 'character_power'
    before_data = member_obj.character_power
    after_data = character_data[field]
    if before_data < after_data:
        add_history(member_obj, field, before_data, after_data)
        member_obj.character_power = character_data[field]
        change_check = 1

    # 생명력
    field = 'character_vitality'
    before_data = member_obj.character_vitality
    after_data = character_data[field]
    if before_data < after_data:
        add_history(member_obj, field, before_data, after_data)
        member_obj.character_vitality = character_data[field]
        change_check = 1

    if change_check:
        member_obj.save()


def add_history(character_obj, field, before_data, after_data):
    History(character_name=character_obj, field=field, before_data=before_data, after_data=after_data).save()
    print(f"character_name: {character_obj.character_name} | field: {field} | before_data: {before_data} | after_data: {after_data}")


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
    # member_obj = Member.objects.filter(character_name=character_name).first()
    # print(member_obj.__dict__)
    # for key, value in member_obj.__dict__.items():
    #     print(key, '|', value)
    character_data = get_member_data(character_name)
    character_data_compare(character_data)



if __name__ == '__main__':
    guild_memeber = ['너와떠나는여행', '채연', '유혈랑', '우유맛조아', '데이지아SR', '남순이견주', '묵련비', '피망꼬치구이', '강배', '명하누', '킹기다킹기', '배천덕', '송저송', '블루밍소설', '신레델라', '그거저아닌데', '배낼', '헵짚', '야레기', '능동로무법자', '메리크리스마스', '커피바드세요', '능동로솜주먹', '퍄닥퍄닥퍄닥퍄닥', '귀여운눈나', 'S순이견주2', '보이드어벤저', '잠옷소년', '추합', '썬연료2', '왜이리더워', '붕슼', '그리워아만', '훈건창', '파이터팽', '꿈꾸세요', '시린미', '대근짱짱', '돈룡', '징징EYA']
    db_member = []
    for member_obj in Member.objects.all():
        db_member.append(member_obj.character_name)
    print(db_member)

    for member_name in guild_memeber:
        character_data = get_member_data(member_name)
        if not character_data: continue
        if member_name not in db_member:
            add_data(character_data)
            print(f'{member_name} data saved')
            print('-----------------------------------')
        else:
            character_data_compare(character_data)
            print(f'{member_name} data compared')
            print('-----------------------------------')

    # test('너와떠나는여행')


    # character_name = '너와떠나는여행'
    # character_data = get_member_data(character_name)

