from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from Surname.models import Dynasty, Province, SecondName
from Surname.services.catalog import load_catalog
from user.models import Comment, Favorite, ReadingHistory

PROVINCES = [
    ("北京市", "beijing", "北京", "北京", "华北", 116.4074, 39.9042),
    ("天津市", "tianjin", "天津", "天津", "华北", 117.2008, 39.0842),
    ("河北省", "hebei", "河北", "河北", "华北", 114.5149, 38.0428),
    ("山西省", "shanxi", "山西", "山西", "华北", 112.5492, 37.8570),
    ("内蒙古自治区", "neimenggu", "内蒙古", "内蒙古", "华北", 111.7492, 40.8426),
    ("辽宁省", "liaoning", "辽宁", "辽宁", "东北", 123.4315, 41.8057),
    ("吉林省", "jilin", "吉林", "吉林", "东北", 125.3235, 43.8171),
    ("黑龙江省", "heilongjiang", "黑龙江", "黑龙江", "东北", 126.6425, 45.7569),
    ("上海市", "shanghai", "上海", "上海", "华东", 121.4737, 31.2304),
    ("江苏省", "jiangsu", "江苏", "江苏", "华东", 118.7969, 32.0603),
    ("浙江省", "zhejiang", "浙江", "浙江", "华东", 120.1551, 30.2741),
    ("安徽省", "anhui", "安徽", "安徽", "华东", 117.2272, 31.8206),
    ("福建省", "fujian", "福建", "福建", "华东", 119.2965, 26.0745),
    ("江西省", "jiangxi", "江西", "江西", "华东", 115.8582, 28.6820),
    ("山东省", "shandong", "山东", "山东", "华东", 117.0009, 36.6512),
    ("河南省", "henan", "河南", "河南", "华中", 113.6254, 34.7466),
    ("湖北省", "hubei", "湖北", "湖北", "华中", 114.3054, 30.5931),
    ("湖南省", "hunan", "湖南", "湖南", "华中", 112.9388, 28.2282),
    ("广东省", "guangdong", "广东", "广东", "华南", 113.2644, 23.1291),
    ("广西壮族自治区", "guangxi", "广西", "广西", "华南", 108.3669, 22.8170),
    ("海南省", "hainan", "海南", "海南", "华南", 110.3312, 20.0311),
    ("重庆市", "chongqing", "重庆", "重庆", "西南", 106.5516, 29.5630),
    ("四川省", "sichuan", "四川", "四川", "西南", 104.0665, 30.5728),
    ("贵州省", "guizhou", "贵州", "贵州", "西南", 106.6302, 26.6477),
    ("云南省", "yunnan", "云南", "云南", "西南", 102.8329, 24.8801),
    ("西藏自治区", "xizang", "西藏", "西藏", "西南", 91.1322, 29.6604),
    ("陕西省", "shaanxi", "陕西", "陕西", "西北", 108.9398, 34.3416),
    ("甘肃省", "gansu", "甘肃", "甘肃", "西北", 103.8343, 36.0611),
    ("青海省", "qinghai", "青海", "青海", "西北", 101.7782, 36.6171),
    ("宁夏回族自治区", "ningxia", "宁夏", "宁夏", "西北", 106.2309, 38.4872),
    ("新疆维吾尔自治区", "xinjiang", "新疆", "新疆", "西北", 87.6168, 43.8256),
    ("香港特别行政区", "hongkong", "香港", "香港", "港澳台", 114.1694, 22.3193),
    ("澳门特别行政区", "macau", "澳门", "澳门", "港澳台", 113.5439, 22.1987),
    ("台湾省", "taiwan", "台湾", "台湾", "港澳台", 121.5654, 25.0330),
]

DYNASTIES = [
    ("夏朝", "xia", 1, -2070, -1600, "约前2070—前1600", "传统史书中的早期王朝。"),
    ("商朝", "shang", 2, -1600, -1046, "约前1600—前1046", "甲骨文与青铜器高度发展的时期。"),
    ("周朝", "zhou", 3, -1046, -256, "前1046—前256", "分封制与礼乐制度影响深远。"),
    ("春秋", "chunqiu", 4, -770, -476, "前770—前476", "诸侯争霸、诸子兴起的时期。"),
    ("战国", "zhanguo", 5, -475, -221, "前475—前221", "列国兼并，最终由秦统一。"),
    ("秦朝", "qin", 6, -221, -207, "前221—前207", "建立中央集权的郡县制。"),
    ("汉朝", "han", 7, -202, 220, "前202—220", "分为西汉与东汉，丝路开通。"),
    ("三国", "sanguo", 8, 220, 280, "220—280", "魏、蜀、吴三足鼎立。"),
    ("晋朝", "jin", 9, 265, 420, "265—420", "分为西晋与东晋，士族南渡。"),
    ("南北朝", "nanbeichao", 10, 420, 589, "420—589", "南北政权长期对峙与融合。"),
    ("隋朝", "sui", 11, 581, 618, "581—618", "重建统一，开凿大运河。"),
    ("唐朝", "tang", 12, 618, 907, "618—907", "经济文化繁荣，中外交流频繁。"),
    ("五代十国", "wudaishiguo", 13, 907, 979, "907—979", "政权更迭频繁的过渡时期。"),
    ("宋朝", "song", 14, 960, 1279, "960—1279", "分为北宋与南宋，文治兴盛。"),
    ("元朝", "yuan", 15, 1271, 1368, "1271—1368", "疆域辽阔，中外交通发达。"),
    ("明朝", "ming", 16, 1368, 1644, "1368—1644", "重建汉族政权，海上交流活跃。"),
    ("清朝", "qing", 17, 1644, 1912, "1644—1912", "最后一个封建王朝。"),
    ("中华民国", "minguo", 18, 1912, 1949, "1912—1949", "近代共和政体时期。"),
]

DEMO_USERS = [
    ("demo", "demo123456", "演示用户"),
    ("reader1", "reader123456", "读者一"),
    ("reader2", "reader123456", "读者二"),
]


class Command(BaseCommand):
    help = "Seed provinces, dynasties, the surname catalog, and demo accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow seeding weak demo passwords outside DEBUG.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_demo 只能在开发环境运行；如确需执行，请加 --force。"
            )
        if not settings.DEBUG:
            self.stdout.write(
                self.style.WARNING(
                    "警告：正在非 DEBUG 环境创建弱口令演示账号。"
                )
            )

        for name, slug, short_name, map_name, region, lng, lat in PROVINCES:
            Province.objects.update_or_create(
                name=name,
                defaults={
                    "slug": slug,
                    "short_name": short_name,
                    "map_name": map_name,
                    "region": region,
                    "center_lng": lng,
                    "center_lat": lat,
                },
            )
        for name, slug, order, begin, end, period_label, description in DYNASTIES:
            Dynasty.objects.update_or_create(
                name=name,
                defaults={
                    "slug": slug,
                    "order": order,
                    "begin": begin,
                    "end": end,
                    "period_label": period_label,
                    "description": description,
                },
            )

        catalog_path = Path(settings.BASE_DIR) / "data" / "catalog.json"
        stats = load_catalog(catalog_path)

        users = {}
        for username, password, display_name in DEMO_USERS:
            user, created = get_user_model().objects.get_or_create(
                username=username
            )
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
            profile = user.profile
            profile.display_name = display_name
            profile.save(update_fields=["display_name"])
            users[username] = user

        user_model = get_user_model()
        demo = users["demo"]
        reader1 = users["reader1"]
        reader2 = users["reader2"]
        li = SecondName.objects.get(second_name="李")
        wang = SecondName.objects.get(second_name="王")
        zhang = SecondName.objects.get(second_name="张")

        Comment.objects.get_or_create(
            user=demo,
            surname=li,
            content="李氏源流资料整理得很清楚，期待更多姓氏。",
        )
        Comment.objects.get_or_create(
            user=reader1,
            surname=wang,
            content="王姓的迁徙路线很适合配合地图阅读。",
        )
        Favorite.objects.get_or_create(user=demo, surname=li)
        Favorite.objects.get_or_create(user=reader1, surname=wang)
        ReadingHistory.objects.update_or_create(
            user=demo, surname=li, defaults={"view_count": 3}
        )
        ReadingHistory.objects.update_or_create(
            user=reader2, surname=zhang, defaults={"view_count": 1}
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据已就绪：{stats.surnames} 个姓氏、{len(DEMO_USERS)} 个账号。"
            )
        )
        self.stdout.write(
            f"演示账号：demo / demo123456（用户模型 {user_model.__name__}）"
        )
