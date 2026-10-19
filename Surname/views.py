import json
import pickle
from pathlib import Path

from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from pyecharts import options as opts
from pyecharts.charts import Map, Timeline

from Surname.models import Dynasty, Province, SecondName

WORD_FILE = Path(__file__).resolve().parent / "static/Surname/model/word"
try:
    with WORD_FILE.open("rb") as handle:
        WORD_ = pickle.load(handle)
except (FileNotFoundError, EOFError, pickle.UnpicklingError):
    # The word-cloud model is generated from the course dataset; the app
    # should still render if it is missing.
    WORD_ = {}

"""
    用于对姓氏的一系列操作进行响应
    Map:用于处理各个姓氏的分布数据的相应
    Surname : 用于处理各个姓氏的基本数据的响应
    wordCloud:用于返回词云图对应的数据
    famous:用于返回对应姓氏的名人信息
    所有函数均需参数: surname(请求数据的姓氏)
    错误返回 : err
"""


class surnameAction(View):
    def get(self, request):
        surname = request.GET.get('surname')
        if not surname:
            response = HttpResponse(json.dumps({'err': "没有姓氏"}), status=400)
            return response
        def deal(content, token, emp):
            value = ""
            for item in (content or "").split(token):
                if emp in item:
                    head, _, tail = item.partition(emp)
                    value += f"<b>{head}</b>{emp}{tail}<br>"
                else:
                    value += f"<b>{item}</b><br>"
            return value
        data = SecondName.objects.filter(second_name=surname)
        if data.count() == 0:
            response = HttpResponse(json.dumps({'err': "没有姓氏"}), status=400)
            return response
        data = data[0]
        data.fam = deal(data.fam , '\n'  ,"：")
        data.cul = deal(data.cul , '\n'  ,"：")
        origin = ""
        for i in data.ori.split('\n'):
            if len(i) <= 5 and '源出' in i:
                origin += '<b>' + i +'</b>'
            else:
                origin += i
            origin += '<br>'
        data.ori = origin
        mapData = self.Map(surname)
        wordCloudData = self.wordCloud(surname)
        treeData = self.famousTree(surname)
        node , link = self.getNeighbor(surname)
        mig = get_dynasty_migration(data.mig)
        tl = None
        if  len(mig):
            tl = Timeline()
            for i in mig:
                tmp_data = []
                for k in mig[i]:
                    tmp_data.append([k , 1])
                map0 = (
                    Map()
                        .add("姓氏路径图", tmp_data, "china")
                        .set_global_opts(
                        visualmap_opts=opts.VisualMapOpts(is_show=False)
                    )
                )
                tl.add(map0, "{}".format(i))
        return render(request, 'surname/index.html', {'surname': data,
                                                      'mapData': mapData,
                                                      'wordCloudData': wordCloudData,
                                                      'treeData': treeData,
                                                      'link' : link,
                                                      'node' : node,
                                                       'graph' : tl.render_embed() if tl else ""})

    """
        用于处理各个姓氏的分布数据的相应
    """

    def Map(self, surname):
        data = SecondName.objects.filter(second_name=surname).first()
        if data is None:
            return {"data": [], "min": 0, "max": 0}
        data.count += 1
        data.save(update_fields=["count"])
        ratio = data.D_surname.all()
        province = Province.objects.all()
        values = []
        minimum = 10000.0
        maximum = 0.0
        for item in province:
            matches = list(ratio & item.D_province.all())
            value = float(matches[0].ratio * 100) if matches else 0.0
            minimum = min(value, minimum)
            maximum = max(value, maximum)
            values.append({"name": item.name.split("省")[0], "value": value})
        if not values:
            minimum = 0.0
        return {"data": values, "min": minimum, "max": maximum}

    """
        用于处理各个姓氏的基本数据的响应
    """

    def Surname(self, surname):
        data = SecondName.objects.filter(second_name=surname)
        content = data[0]
        content.count += 1
        content.save()
        data = {}
        for i in SecondName._meta.fields:
            data[str(i).split('.')[-1]] = content.serializable_value(str(i).split('.')[-1])
        return data

    """
        用于返回词云图对应的数据
    """

    def wordCloud(self, surname):
        raw = WORD_.get(surname, [])
        return [
            {"name": str(item.get("name", "")), "value": float(item.get("value", 0))}
            for item in raw
        ]

    """
        用于返回对应姓氏的名人信息
    """

    def famousTree(self, surname):
        data = SecondName.objects.filter(second_name=surname)
        data = data[0]
        data.count += 1
        data.save()
        people = data.F_surname.all()
        dynasty = Dynasty.objects.all()
        data = []
        for j in dynasty:
            tmp = people & j.F_dynasty.all()
            content = {}
            content['value'] = tmp.count()
            content['name'] = j.name
            if tmp.count():
                content['children'] = []
                for k in tmp:
                    children = {}
                    children['name'] = k.name
                    children['value'] = 1
                    content['children'].append(children)
            data.append(content)
        return data

    def getNeighbor(self,surname):
        data = SecondName.objects.filter(second_name=surname)
        data = data[0]
        node = []
        link = []
        for i in data.father_surname.all():
            if i.second_name == surname:
                continue
            node.append({"name" : i.second_name , "symbolSize": 10})
            link.append({"source" : i.second_name , "target" : surname , 'relation' : {'name' : "祖先"}})
        # for i in data.children.all():
        #     if i.second_name == surname:
        #         continue
        #     node.append({'name': i.second_name, "value": 10})
        #     link.append({'source': surname, 'target': i.second_name})
        node.append({"name": surname, "symbolSize": 50})
        return [node , link]
    def announce(request):
        return render(request , 'surname/announce.html')
    def developer(request):
        return render(request , 'surname/developer.html')
    def information(request):
        return render(request , 'surname/information.html')
    def introduction(request):
        return render(request , 'surname/introduction.html')
    def origin(request):
        return render(request , 'surname/origin.html')
    def science(request):
        return render(request , 'surname/science.html')
    def search(request):
        top = SecondName.objects.all()
        top = top.order_by('-count')
        return render(request , 'surname/search.html' , {'hot' : top[:10]})

def split_sents(para: str):
    sents = []
    start_ind = 0
    for i in range(len(para)):
        w = para[i]
        if w == '。' or w == ';' or w == '\r':
            if i > start_ind:
                s = para[start_ind:i]
                if s != '':
                    sents.append(s)
            if w == '\r':
                i += 1
            start_ind = i + 1

    if len(para) > start_ind:
        s = para[start_ind:]
        if s != '':
            sents.append(s)

    return sents


def get_dynasty_migration(migration_history, show_details=False):
    migration_history = migration_history or ""
    dynasties_find = '夏,商,周,秦,汉,三国,晋,南朝,北朝,南北朝,隋,唐,五代,十国,宋,金,元,明,清,民国'.split(',')
    dynasties = '夏朝,商（殷）朝,周朝,春秋战国,秦朝,汉朝,三国时期,晋朝,南北朝,隋朝,唐朝,五代十国,宋朝,元朝,明朝,清朝,中华民国,中华人民共和国'.split(',')
    provinces = '内蒙古,新疆,广西,西藏,重庆,北京,天津,澳门,香港,河北,山西,吉林,辽宁,黑龙江,陕西,甘肃,青海,' \
                '山东,福建,浙江,台湾,河南,湖北,湖南,江西,江苏,安徽,广东,海南,四川,贵州,云南,宁夏,上海'.split(',')

    sents = split_sents(migration_history)
    migration_locations = {}
    # dynasty_locations = []
    validation = []
    time_ind = 0
    for i in range(len(sents)):
        s = sents[i]

        find_dynasties = []
        for dy_ind, d in enumerate(dynasties_find):
            if d in s and dy_ind >= time_ind:
                find_dynasties.append(d)
                time_ind = dy_ind

        if len(find_dynasties) == 0:
            continue

        find_provinces = []
        for p in provinces:
            if p in s:
                find_provinces.append(p)

        if len(find_provinces) == 0:
            continue

        for d in find_dynasties:
            for p in find_provinces:
                for dy in dynasties:
                    if d in dy:
                        loc_set = migration_locations.setdefault(dy, [])
                        loc_set.append(p)
        validation.append([s, find_dynasties, find_provinces])

    if show_details:
        for item in validation:
            print(item)
    return migration_locations
