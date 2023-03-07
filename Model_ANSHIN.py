import googlemaps
import os
from dotenv import load_dotenv
from math import log
from math import tan
from math import pi
import io
from urllib import request
from urllib import error
from PIL import Image
import requests

# 洪水の浸水深さのrgbリスト作成
kozui_img_rgb = [ [0,0,0],
                  [247,245,169],
                  [255,216,192],
                  [255,183,183],
                  [255,145,145],
                  [242,133,201],
                  [220,122,220]
                 ]
# 津波、高潮の浸水深さのrgbリスト作成（洪水）
tunami_takashio_img_rgb = [ [0,0,0],
                            [255,255,179],
                            [247,245,169],
                            [248,225,166],
                            [255,216,192],
                            [255,183,183],
                            [255,145,145],
                            [242,133,201],
                            [220,122,188]
                           ]
# 浸水深さのrgbリストのリスト
shinsui_hazard_img = [kozui_img_rgb,tunami_takashio_img_rgb,tunami_takashio_img_rgb]

# 洪水の浸水深さのハザードリスト作成
kozui_hazard = [ '0.1m未満',
                 '0.5m未満',
                 '0.5~3.0m',
                 '3.0~5.0m',
                 '5.0~10.0m',
                 '10.0~20.0m',
                 '20m以上'
                ]
# 津波、高潮の浸水深さのハザードリスト作成
tunami_takashio_hazard = [ 'なし',
                           '0.3m未満',
                           '0.3~0.5m',
                           '0.5~1.0m',
                           '1.0~3.0m',
                           '3.0~5.0m',
                           '5.0~10.0m',
                           '10.0~20.0m',
                           '20m以上'
                          ]
# 浸水深さのハザードリストのリスト
shinsui_hazard = [kozui_hazard,tunami_takashio_hazard,tunami_takashio_hazard]

# 浸水深さハザードのタイル画像のurl
# 洪水浸水想定区域（想定最大規模）：
# https://disaportaldata.gsi.go.jp/raster/01_flood_l2_shinsuishin_data/{z}/{x}/{y}.png
# 津波浸水想定
# https://disaportaldata.gsi.go.jp/raster/04_tsunami_newlegend_data/{z}/{x}/{y}.png
# 高潮浸水想定区域
# https://disaportaldata.gsi.go.jp/raster/03_hightide_l2_shinsuishin_data/{z}/{x}/{y}.png
hazard_url_list = [ "01_flood_l2_shinsuishin_data/",
                    "04_tsunami_newlegend_data/",
                    "03_hightide_l2_shinsuishin_data/"
                   ] 

# ◯緯度経度取得 by googlemap API
# INPUT:住所、物件名、googlemapのAPI_KEY
# OUTPUT:緯度、経度のリスト
# 下記使用例：
# address="大阪府大阪市北区万歳町"
# name = "ロジュマンタワー梅田"
# latlng_list = get_gmap_latlng(address,name)
# print(latlng_list) 
# [34.70516, 135.5044608]
def get_gmap_latlng(address, name):
    load_dotenv()
    MAP_API_KEY =  os.getenv('MY_MAP_API_KEY')
    gm = googlemaps.Client(key=MAP_API_KEY)
    res = gm.geocode(address+' '+name)
    return [res[0]['geometry']['location']['lat'],res[0]['geometry']['location']['lng']]

# 緯度経度をタイル座標へ変換する関数
# INPUT:緯度、経度、Zoomレベル 
# OUTPUT:xのタイル座標、yのタイル座標
def latlon2tile(lon, lat, z):
    x = int((lon / 180 + 1) * 2**z / 2) # x座標
    y = int(((-log(tan((45 + lat / 2) * pi / 180)) + pi) * 2**z / (2 * pi))) # y座標
    return [x,y]

# ◯緯度経度をタイル座標、ピクセル座標へ変換する関数
# INPUT:Zoomレベル、緯度、経度 
# OUTPUT:xのタイル座標(Zoom17)、yのタイル座標(Zoom17)、xのピクセル座標、yのピクセル座標
# 下記使用例：
# lat = 34.70516
# lng = 135.5044608
# tile_pixel_list = get_tile_pixel(lat,lng)
# print(tile_pixel_list)
# [114871, 52048, 171, 37]
def get_tile_pixel(lat,lng):
    # タイル座標取得：タイル地図の取得用(Zoomレベル=17)
    z =17
    [x_tile_17,y_tile_17] = latlon2tile(lng, lat, z)
    # 詳細タイル座標取得(Zoomレベル=25)
    z = 25
    [x_tile_25,y_tile_25] = latlon2tile(lng, lat, z)
    # ピクセル位置生成
    x_pixel = x_tile_25 - x_tile_17*256
    y_pixel = y_tile_25 - y_tile_17*256
    return [x_tile_17,y_tile_17,x_pixel,y_pixel]

# ◯ハザードレベル取得(浸水深さ)
# INPUT:ハザードの種類(0:洪水、1:津波、2:高潮)、xのタイル座標(Zoom17)、yのタイル座標(Zoom17)、xのピクセル座標、yのピクセル座標
# OUTPUT:[ハザードレベル,浸水深さ](リスト型)
# 下記使用例：
# i_hazard = 0 (洪水)
# x_tile = 114871
# y_tile = 52048
# x_pixel = 171 (0~255)
# y_pixel = 37  (0~255)
# hazard = shisui_hazard_level(i_hazard, x_tile, y_tile,x_pixel,y_pixel)
# print(hazard)
# [2, '0.5~3.0m']
def shisui_hazard_level(i_hazard, x_tile, y_tile,x_pixel,y_pixel):
    # ハザードタイル画像の取得
    hazard_url = hazard_url_list[i_hazard]
    tile_coordinate = str(17) + '/' + str(x_tile)+'/'+ str(y_tile)
    url = 'https://disaportaldata.gsi.go.jp/raster/{0}{1}.png'.format(hazard_url,tile_coordinate)
    # print(url)
    try:
        # 画像読み込み    
        f = io.BytesIO(request.urlopen(url).read())
        img = Image.open(f)
        # rgbデータ取得 (ピクセル数指定)
        r,g,b,a = img.getpixel((x_pixel,y_pixel))
        rgb_list = [r,g,b]
    except error.URLError as e:
        rgb_list = [0,0,0]
    # print(rgb_list)
    # ハザードレベルに変換
    shinshi_level = shinsui_hazard_img[i_hazard].index(rgb_list)
    return [shinshi_level, shinsui_hazard[i_hazard][shinshi_level]]

# 土砂災害のrgbリスト作成
# ①急傾斜地の崩壊（なし、危険箇所、警戒区域、特別警戒区域）
kyukeisya_img_rgb = [ [0,0,0],
                      [224,224,254],
                      [250,231,0],
                      [250,40,0]
                    ]
# ②土石流（なし、危険箇所、警戒区域、特別警戒区域）
dosekiryu_img_rgb = [ [0,0,0],
                      [245,153,101],
                      [230,200,50],
                      [165,0,33]
                    ]
# ③地滑り（なし、危険箇所、警戒区域、特別警戒区域）
jisuberi_img_rgb = [  [0,0,0],
                      [255,235,223],
                      [255,153,0],
                      [180,0,40]
                    ]

# 土砂災害のrgbリストのリスト
dosya_hazard_img_list=[kyukeisya_img_rgb,dosekiryu_img_rgb,jisuberi_img_rgb]

# 土砂災害（危険箇所、警戒区域、特別警戒区域）のタイル画像のurl
# ⓪急傾斜地崩壊危険箇所
# https://disaportaldata.gsi.go.jp/raster/05_kyukeisyachihoukai/{z}/{x}/{y}.png
# 土砂災害警戒区域（急傾斜地の崩壊）
# https://disaportaldata.gsi.go.jp/raster/05_kyukeishakeikaikuiki/{z}/{x}/{y}.png

# ①土石流危険渓流
# https://disaportaldata.gsi.go.jp/raster/05_dosekiryukikenkeiryu/{z}/{x}/{y}.png
# 土砂災害警戒区域（土石流）
# https://disaportaldata.gsi.go.jp/raster/05_dosekiryukeikaikuiki/{z}/{x}/{y}.png 

# ②地すべり危険箇所
# https://disaportaldata.gsi.go.jp/raster/05_jisuberikikenkasyo/{z}/{x}/{y}.png
# 土砂災害警戒区域（地すべり）
# https://disaportaldata.gsi.go.jp/raster/05_jisuberikeikaikuiki/{z}/{x}/{y}.png

# 土砂災害の危険箇所のURLリスト
dosya_danger_url_list = [ "05_kyukeisyachihoukai/",   # 急傾斜地の崩壊
                          "05_dosekiryukikenkeiryu/", # 土石流
                          "05_jisuberikikenkasyo/"    # 地すべり
                        ]

# 土砂災害の警戒区域、特別警戒区域のURLリスト
dosya_alert_url_list = [ "05_kyukeishakeikaikuiki/", # 急傾斜地の崩壊
                         "05_dosekiryukeikaikuiki/", # 土石流
                         "05_jisuberikeikaikuiki/"   # 地すべり
                        ]
# 土砂災害：区域名称リスト
dosya_hazard_name_list = [ ["なし","危険箇所","警戒区域","特別警戒区域"], # 急傾斜地の崩壊
                           ["なし","危険渓流","警戒区域","特別警戒区域"], # 土石流
                           ["なし","危険箇所","警戒区域","特別警戒区域"]  # 地すべり
                         ]

# ◯ハザードレベル変換（土砂災害)
# INPUT:ハザードの種類(0:急傾斜地の崩壊、1:土石流、2:地すべり)、xのタイル座標(Zoom17)、yのタイル座標(Zoom17)、xのピクセル座標、yのピクセル座標
# OUTPUT:[ハザードレベル,名称]（[0,なし]、[1,危険箇所]、[2,警戒区域]、[3,特別警戒区域])
# 下記使用例：
# i_hazard =1 (土石流)
# x_tile = 114926
# y_tile = 52059
# x_pixel = 50 (0~255)
# y_pixel = 50 (0~255)
# dosya_hazard = mod.dosya_hazard_level(i_hazard, x_tile, y_tile,x_pixel,y_pixel)
# print(dosya_hazard)
# [2, '警戒区域']
def dosya_hazard_level(i_hazard, x_tile, y_tile,x_pixel,y_pixel):
    # ハザードタイル画像の取得
    tile_coordinate = str(17) + '/' + str(x_tile)+'/'+ str(y_tile)
    # 危険箇所のurl
    danger_url_part = dosya_danger_url_list[i_hazard]
    danger_url = 'https://disaportaldata.gsi.go.jp/raster/{0}{1}.png'.format(danger_url_part,tile_coordinate)
    # 警戒区域、特別警戒区域のurl
    alert_url_part = dosya_alert_url_list[i_hazard]
    alert_url = 'https://disaportaldata.gsi.go.jp/raster/{0}{1}.png'.format(alert_url_part,tile_coordinate)
    # print(alert_url)
    # 画像が取得できた場合は、警戒区域、特別警戒区域：画像読み込み
    try:
        request.urlopen(alert_url)
        f = io.BytesIO(request.urlopen(alert_url).read())
        img = Image.open(f)
        # rgbデータ取得 (ピクセル数指定)
        r,g,b,a = img.getpixel((x_pixel,y_pixel))
        rgb_list = [r,g,b]
        err_check = False
        # print(rgb_list)
    except error.URLError as e:
        # print(e.code)
        err_check = True
        # pass
    # 画像が取得できない場合、もしくは[0,0,0]の場合は、危険箇所の画像をチェック
    if err_check or rgb_list == [0,0,0]:
        try:
            # print(danger_url)
            f = io.BytesIO(request.urlopen(danger_url).read())
            img = Image.open(f)
            # rgbデータ取得 (ピクセル数指定)
            r,g,b,a = img.getpixel((x_pixel,y_pixel))
            rgb_list = [r,g,b]
        except error.URLError as e:
            # print(e.code)
            rgb_list = [0,0,0]
            # pass
    # print(rgb_list)    
    # ハザードレベルに変換
    dosya_hazard_level = dosya_hazard_img_list[i_hazard].index(rgb_list)
    return [dosya_hazard_level,dosya_hazard_name_list[i_hazard][dosya_hazard_level]]

# ◯今後30年の震度の確率を取得(by地震API:2022年版/最大ケース/すべての地震/geojson形式）
# https://www.j-shis.bosai.go.jp/api-pshm-meshinfo
# INPUT:緯度、経度
# OUTPUT:最大ケースで今後30年の震度①~⑤の確率[%]（リスト型：①震度4以下、②震度5弱、③震度5強、④震度6弱、⑤震度6強以上）
# 下記使用例：
# lat = 34.70516
# lng = 135.5044608
# shindo_list = get_earthquake_API(lat,lng)
# print(shindo_list)
# [9.877, 15.636, 41.813, 26.313, 6.361]
def get_earthquake_API(lat,lng):
    position = str(lng)+","+str(lat)
    url = "https://www.j-shis.bosai.go.jp/map/api/pshm/Y2022/MAX/TTL_MTTL/meshinfo.geojson?position={}&epsg=4612".format(position)
    result = requests.get(url).json()
    if result["status"] == "Success":
        shindo_l45=float(result['features'][0]['properties']['T30_I45_PS'])
        shindo_l50=float(result['features'][0]['properties']['T30_I50_PS'])
        shindo_l55=float(result['features'][0]['properties']['T30_I55_PS'])
        shindo_l60=float(result['features'][0]['properties']['T30_I60_PS'])

        shindo_less_40 = round((1.0 - shindo_l45)*100,3)
        shindo_45 = round((shindo_l45 - shindo_l50)*100,3)
        shindo_50 = round((shindo_l50 - shindo_l55)*100,3)
        shindo_55 = round((shindo_l55 - shindo_l60)*100,3)
        shindo_more_60 = round(shindo_l60*100,3)
        shindo_list = [shindo_less_40,shindo_45,shindo_50,shindo_55,shindo_more_60]
        return shindo_list
    else:
        return None

# get_earthquake_APIのOUTPUTから確率が最も高いレベルを選択
# INPUT:震度レベル①〜⑤の確率(リスト型)
# OUTPUT:[最大確率のハザードレベル,その震度名,その確率(%)] (リスト型)
# 下記使用例：
# shindo_list = [9.877, 15.636, 41.813, 26.313, 6.361]
# print(earthquake_rank(shindo_list))
# [2, '震度5強', 41.813]
earthquake_hazard_name_list = ["震度4以下", "震度5弱", "震度5強", "震度6弱", "震度6強以上"]
def earthquake_rank(shindo_list):
    # リストのがNoneじゃない場合実行
    if shindo_list:
        max_value = max(shindo_list)
        hazard_level = shindo_list.index(max_value)
        hazard_name = earthquake_hazard_name_list[hazard_level]
        return [hazard_level,hazard_name,max_value]
