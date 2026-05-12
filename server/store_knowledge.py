"""Static store knowledge for Carrefour (家樂福) supermarket layout and product search."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class AisleInfo:
    number: int
    categories_zh: List[str]
    categories_en: List[str]
    products_zh: List[str] = field(default_factory=list)
    products_en: List[str] = field(default_factory=list)


@dataclass
class ZoneInfo:
    name: str
    display_name_zh: str
    display_name_en: str
    categories_zh: List[str] = field(default_factory=list)
    categories_en: List[str] = field(default_factory=list)
    products_zh: List[str] = field(default_factory=list)
    products_en: List[str] = field(default_factory=list)
    adjacent_aisles: List[int] = field(default_factory=list)


@dataclass
class LocationMatch:
    location_type: str  # "aisle" or "zone"
    aisle_number: Optional[int]
    zone_name: Optional[str]
    display_en: str
    display_zh: str
    matched_keyword: str
    confidence: float


# ---------------------------------------------------------------------------
# Aisle data (verified from front-facing store signage photos)
# ---------------------------------------------------------------------------
AISLES: List[AisleInfo] = [
    AisleInfo(
        number=1,
        categories_zh=["堅果", "肉乾", "海苔"],
        categories_en=["Nuts", "Jerky", "Seaweed"],
        products_zh=["堅果", "核桃", "杏仁", "腰果", "花生", "開心果", "夏威夷豆",
                      "肉乾", "豬肉乾", "牛肉乾", "魷魚絲", "海苔", "紫菜"],
        products_en=["nuts", "walnut", "almond", "cashew", "peanut", "pistachio",
                      "macadamia", "jerky", "beef jerky", "pork jerky", "dried meat",
                      "squid", "seaweed", "nori"],
    ),
    AisleInfo(
        number=2,
        categories_zh=["茶", "汽水", "咖啡", "果汁"],
        categories_en=["Tea", "Soda", "Coffee", "Juice"],
        products_zh=["茶", "綠茶", "紅茶", "烏龍茶", "汽水", "可樂", "雪碧",
                      "咖啡", "即溶咖啡", "三合一", "果汁", "柳橙汁", "蘋果汁",
                      "運動飲料", "能量飲料", "礦泉水", "氣泡水"],
        products_en=["tea", "green tea", "black tea", "oolong", "soda", "cola",
                      "coke", "pepsi", "sprite", "coffee", "instant coffee",
                      "juice", "orange juice", "apple juice", "sports drink",
                      "energy drink", "mineral water", "sparkling water"],
    ),
    AisleInfo(
        number=3,
        categories_zh=["糖果", "巧克力"],
        categories_en=["Candy", "Chocolate"],
        products_zh=["糖果", "軟糖", "硬糖", "棒棒糖", "口香糖", "薄荷糖",
                      "巧克力", "黑巧克力", "牛奶巧克力", "白巧克力"],
        products_en=["candy", "gummy", "lollipop", "chewing gum", "mint",
                      "chocolate", "dark chocolate", "milk chocolate",
                      "white chocolate", "sweets", "toffee"],
    ),
    AisleInfo(
        number=4,
        categories_zh=["紙尿褲", "衛生棉", "廚房用品"],
        categories_en=["Diapers", "Feminine Hygiene", "Kitchenware"],
        products_zh=["紙尿褲", "尿布", "衛生棉", "護墊", "廚房用品",
                      "保鮮膜", "鋁箔紙", "垃圾袋", "手套", "烘焙紙"],
        products_en=["diaper", "nappy", "sanitary pad", "panty liner",
                      "feminine hygiene", "kitchenware", "plastic wrap",
                      "aluminum foil", "trash bags", "gloves", "baking paper"],
    ),
    AisleInfo(
        number=5,
        categories_zh=["米果", "蘇打餅"],
        categories_en=["Rice Crackers", "Soda Crackers"],
        products_zh=["米果", "蘇打餅", "仙貝", "雪餅", "旺旺"],
        products_en=["rice cracker", "soda cracker", "rice puff",
                      "senbei", "arare"],
    ),
    AisleInfo(
        number=6,
        categories_zh=["身體清潔", "髮類清潔", "家庭保健", "臉部護理",
                        "口腔護理", "洗髮精", "沐浴乳", "洗手乳"],
        categories_en=["Body Care", "Hair Care", "Family Hygiene",
                        "Face Care", "Oral Care", "Shampoo", "Body Wash", "Hand Wash"],
        products_zh=["洗髮精", "潤髮乳", "護髮", "沐浴乳", "肥皂", "洗手乳",
                      "牙膏", "牙刷", "漱口水", "洗面乳", "卸妝",
                      "保養品", "面膜", "乳液"],
        products_en=["shampoo", "conditioner", "hair care", "body wash", "soap",
                      "hand wash", "shower gel", "toothpaste", "toothbrush",
                      "mouthwash", "face wash", "makeup remover",
                      "skincare", "face mask", "lotion"],
    ),
    AisleInfo(
        number=7,
        categories_zh=["洋芋片"],
        categories_en=["Chips"],
        products_zh=["洋芋片", "薯片", "蝦餅"],
        products_en=["chips", "crisps", "potato chips", "shrimp crackers"],
    ),
    AisleInfo(
        number=8,
        categories_zh=["內衣", "襪子", "毛巾", "洗衣精", "洗衣粉", "漂白水"],
        categories_en=["Underwear", "Socks", "Towel", "Laundry Liquid",
                        "Laundry Powder", "Bleach"],
        products_zh=["內衣", "襪子", "毛巾", "洗衣精", "洗衣粉", "柔軟精",
                      "漂白水", "衣架", "曬衣夾"],
        products_en=["underwear", "socks", "towel", "laundry detergent",
                      "laundry liquid", "laundry powder", "fabric softener",
                      "bleach", "hanger", "clothespin"],
    ),
    AisleInfo(
        number=9,
        categories_zh=["點心"],
        categories_en=["Snack"],
        products_zh=["點心", "零食", "餅乾", "薯條", "玉米片"],
        products_en=["snack", "snacks", "biscuit", "fries", "doritos",
                      "corn chips", "tortilla chips"],
    ),
    AisleInfo(
        number=10,
        categories_zh=["家用清潔", "家用五金"],
        categories_en=["Housekeeping", "Houseware"],
        products_zh=["清潔劑", "拖把", "掃把", "抹布", "菜瓜布", "海綿",
                      "殺蟲劑", "蚊香", "芳香劑", "除臭劑",
                      "五金", "工具", "電池", "燈泡"],
        products_en=["cleaner", "cleaning", "mop", "broom", "rag", "sponge",
                      "scrubber", "insecticide", "bug spray", "mosquito coil",
                      "air freshener", "deodorizer",
                      "hardware", "tools", "battery", "batteries", "light bulb"],
    ),
    AisleInfo(
        number=11,
        categories_zh=["夾心餅", "泡芙"],
        categories_en=["Sandwich Biscuit", "Puff"],
        products_zh=["夾心餅", "夾心酥", "威化餅", "泡芙", "蛋捲"],
        products_en=["sandwich biscuit", "wafer", "cream puff", "puff",
                      "egg roll"],
    ),
    AisleInfo(
        number=12,
        categories_zh=["泡麵"],
        categories_en=["Instant Noodles"],
        products_zh=["泡麵", "杯麵", "速食麵", "拉麵", "乾麵"],
        products_en=["instant noodle", "instant noodles", "cup noodle",
                      "ramen", "instant ramen"],
    ),
    AisleInfo(
        number=13,
        categories_zh=["進口食品", "甜餅乾"],
        categories_en=["Imported Food", "Sweet Biscuit"],
        products_zh=["進口食品", "進口零食", "甜餅乾", "曲奇", "奶油餅乾"],
        products_en=["imported food", "import", "sweet biscuit",
                      "cookie", "cookies", "butter cookie"],
    ),
    AisleInfo(
        number=14,
        categories_zh=["麵條", "進口食品", "罐頭食品"],
        categories_en=["Cooking Noodles", "Imported Food", "Canned Food"],
        products_zh=["麵條", "義大利麵", "冬粉", "米粉", "麵線",
                      "進口食品", "罐頭", "罐頭食品", "鮪魚罐頭",
                      "玉米罐頭", "水果罐頭"],
        products_en=["noodle", "noodles", "pasta", "spaghetti", "vermicelli",
                      "rice noodle", "imported food", "canned food",
                      "canned tuna", "canned corn", "canned fruit"],
    ),
    AisleInfo(
        number=15,
        categories_zh=["早餐食品", "南北貨"],
        categories_en=["Breakfast", "Sundry Food"],
        products_zh=["早餐", "早餐食品", "麥片", "穀物", "燕麥", "果醬",
                      "南北貨", "乾貨", "香菇", "木耳", "紅棗", "枸杞"],
        products_en=["breakfast", "breakfast food", "cereal", "oats", "oatmeal",
                      "jam", "marmalade", "sundry food", "dried goods",
                      "dried mushroom", "dried fungus", "jujube", "goji berry"],
    ),
    AisleInfo(
        number=16,
        categories_zh=["米", "調理食品", "調味品"],
        categories_en=["Rice", "Ready-to-cook Food", "Seasoning"],
        products_zh=["米", "白米", "糙米", "五穀米", "調理食品", "調理包",
                      "調味品", "鹽", "糖", "胡椒", "醬油", "醋",
                      "料理米酒", "沙茶醬", "番茄醬", "辣椒醬"],
        products_en=["rice", "white rice", "brown rice", "grain",
                      "ready to cook", "cooking pack", "meal kit",
                      "seasoning", "salt", "sugar", "pepper", "soy sauce",
                      "vinegar", "cooking wine", "ketchup", "chili sauce",
                      "hot sauce"],
    ),
    AisleInfo(
        number=17,
        categories_zh=["茶類", "穀料"],
        categories_en=["Tea", "Cereal", "Grain"],
        products_zh=["茶葉", "茶包", "花茶", "普洱茶", "高山茶",
                      "穀料", "穀粉", "奶粉", "可可", "沖泡"],
        products_en=["loose tea", "tea bags", "flower tea", "pu-erh tea",
                      "high mountain tea", "cereal", "grain powder",
                      "milk powder", "cocoa", "instant drink"],
    ),
    AisleInfo(
        number=18,
        categories_zh=["鮮奶", "豆漿", "果汁", "甜點"],
        categories_en=["Fresh Milk", "Soy Milk", "Juice", "Desserts"],
        products_zh=["鮮奶", "牛奶", "豆漿", "優酪乳", "優格", "果汁", "甜點",
                      "布丁", "果凍", "蛋糕"],
        products_en=["fresh milk", "milk", "soy milk", "yogurt", "yoghurt",
                      "juice", "dessert", "pudding", "jelly", "cake"],
    ),
]

# ---------------------------------------------------------------------------
# Perimeter zones
# ---------------------------------------------------------------------------
ZONES: List[ZoneInfo] = [
    ZoneInfo(
        name="entrance",
        display_name_zh="入口/促銷區",
        display_name_en="Entrance / Promotions",
        categories_zh=["促銷", "飲料", "水"],
        categories_en=["Promotions", "Drinks", "Water"],
        products_zh=["促銷商品", "礦泉水", "箱裝飲料", "衛生紙"],
        products_en=["promotions", "bulk water", "boxed drinks", "tissue paper",
                      "toilet paper"],
        adjacent_aisles=[1, 2],
    ),
    ZoneInfo(
        name="left_wall_fresh",
        display_name_zh="左側牆 - 生鮮蔬果區",
        display_name_en="Left wall - Fresh Produce",
        categories_zh=["生鮮", "蔬菜", "水果", "野菜"],
        categories_en=["Fresh produce", "Vegetables", "Fruits"],
        products_zh=["蔬菜", "青菜", "高麗菜", "花椰菜", "紅蘿蔔", "洋蔥",
                      "番茄", "馬鈴薯", "水果", "蘋果", "香蕉", "橘子",
                      "鳳梨", "芒果", "葡萄", "西瓜"],
        products_en=["vegetables", "cabbage", "broccoli", "carrot", "onion",
                      "tomato", "potato", "fruit", "apple", "banana", "orange",
                      "pineapple", "mango", "grape", "watermelon", "lettuce"],
        adjacent_aisles=[1, 2, 3],
    ),
    ZoneInfo(
        name="left_wall_hotpot",
        display_name_zh="左側牆 - 火鍋/冷藏區",
        display_name_en="Left wall - Hotpot / Refrigerated",
        categories_zh=["火鍋料", "火鍋肉片", "冷藏食品", "豆腐", "鮮肉"],
        categories_en=["Hotpot ingredients", "Hotpot meat", "Refrigerated food", "Tofu", "Fresh meat"],
        products_zh=["火鍋料", "火鍋肉片", "牛肉片", "豬肉片", "羊肉片",
                      "豆腐", "豆皮", "丸子", "魚板", "蟹肉棒",
                      "冷藏食品", "鮮肉", "雞肉", "豬肉", "牛肉", "海鮮",
                      "蝦", "魚"],
        products_en=["hotpot", "hot pot", "meat slices", "beef slices",
                      "pork slices", "lamb slices", "tofu", "bean curd",
                      "meatball", "fish cake", "crab stick",
                      "fresh meat", "chicken", "pork", "beef", "seafood",
                      "shrimp", "fish"],
        adjacent_aisles=[15, 16, 17, 18],
    ),
    ZoneInfo(
        name="back_wall",
        display_name_zh="後方牆 - 冷凍/酒類區",
        display_name_en="Back wall - Frozen / Alcohol",
        categories_zh=["冷凍食品", "冰淇淋", "啤酒", "酒類"],
        categories_en=["Frozen food", "Ice cream", "Beer", "Alcohol"],
        products_zh=["冷凍食品", "冷凍水餃", "冷凍蔬菜", "冰淇淋", "冰棒",
                      "啤酒", "台灣啤酒", "紅酒", "白酒", "威士忌", "清酒"],
        products_en=["frozen food", "frozen dumpling", "frozen vegetables",
                      "ice cream", "popsicle", "beer", "taiwan beer", "wine",
                      "red wine", "white wine", "whiskey", "sake", "alcohol",
                      "liquor"],
        adjacent_aisles=[17, 18],
    ),
]


# ---------------------------------------------------------------------------
# Product search
# ---------------------------------------------------------------------------
def _is_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def find_product(query: str) -> List[LocationMatch]:
    """Find where a product is located in the store.

    Accepts Chinese or English queries. Returns a ranked list of matches.
    """
    query_lower = query.lower().strip()
    results: List[LocationMatch] = []

    # Search aisles
    for aisle in AISLES:
        best_score = 0.0
        best_keyword = ""

        # Choose search lists based on query language
        if _is_cjk(query_lower):
            search_lists = [
                (aisle.categories_zh, 1.0),
                (aisle.products_zh, 0.9),
            ]
        else:
            search_lists = [
                (aisle.categories_en, 1.0),
                (aisle.products_en, 0.9),
            ]

        for word_list, base_score in search_lists:
            for keyword in word_list:
                kw_lower = keyword.lower()
                # Exact match
                if query_lower == kw_lower:
                    score = base_score
                # Query is substring of keyword or vice versa
                elif query_lower in kw_lower or kw_lower in query_lower:
                    score = base_score * 0.8
                else:
                    # Fuzzy match
                    ratio = difflib.SequenceMatcher(None, query_lower, kw_lower).ratio()
                    if ratio > 0.55:
                        score = base_score * ratio * 0.7
                    else:
                        continue

                if score > best_score:
                    best_score = score
                    best_keyword = keyword

        if best_score > 0:
            cats_en = " / ".join(aisle.categories_en[:4])
            cats_zh = " / ".join(aisle.categories_zh[:4])
            results.append(LocationMatch(
                location_type="aisle",
                aisle_number=aisle.number,
                zone_name=None,
                display_en=f"Aisle {aisle.number} - {cats_en}",
                display_zh=f"走道{aisle.number} - {cats_zh}",
                matched_keyword=best_keyword,
                confidence=best_score,
            ))

    # Search zones
    for zone in ZONES:
        best_score = 0.0
        best_keyword = ""

        if _is_cjk(query_lower):
            search_lists = [
                (zone.categories_zh, 1.0),
                (zone.products_zh, 0.9),
            ]
        else:
            search_lists = [
                (zone.categories_en, 1.0),
                (zone.products_en, 0.9),
            ]

        for word_list, base_score in search_lists:
            for keyword in word_list:
                kw_lower = keyword.lower()
                if query_lower == kw_lower:
                    score = base_score
                elif query_lower in kw_lower or kw_lower in query_lower:
                    score = base_score * 0.8
                else:
                    ratio = difflib.SequenceMatcher(None, query_lower, kw_lower).ratio()
                    if ratio > 0.55:
                        score = base_score * ratio * 0.7
                    else:
                        continue

                if score > best_score:
                    best_score = score
                    best_keyword = keyword

        if best_score > 0:
            results.append(LocationMatch(
                location_type="zone",
                aisle_number=None,
                zone_name=zone.name,
                display_en=zone.display_name_en,
                display_zh=zone.display_name_zh,
                matched_keyword=best_keyword,
                confidence=best_score,
            ))

    results.sort(key=lambda m: m.confidence, reverse=True)
    return results


def get_all_aisles() -> List[dict]:
    """Return a summary of all aisles for the /store/aisles endpoint."""
    return [
        {
            "number": a.number,
            "categories_zh": a.categories_zh,
            "categories_en": a.categories_en,
        }
        for a in AISLES
    ]


def get_all_zones() -> List[dict]:
    """Return a summary of all perimeter zones."""
    return [
        {
            "name": z.name,
            "display_name_zh": z.display_name_zh,
            "display_name_en": z.display_name_en,
            "categories_zh": z.categories_zh,
            "categories_en": z.categories_en,
        }
        for z in ZONES
    ]
