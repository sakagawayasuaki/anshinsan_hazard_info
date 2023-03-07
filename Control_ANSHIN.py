import Model_ANSHIN as mod
import pandas as pd
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()
MAP_API_KEY =  os.getenv('MY_MAP_API_KEY')


def get_disaster_info_from_address(address, name):
    # 住所から緯度経度、タイル、ピクセル座標を取得
    # address = option + municipality
    # name = propertyname 
    lat, lng = mod.get_gmap_latlng(address, name)
    tile_pixel_list = mod.get_tile_pixel(lat, lng)
    x_tile = tile_pixel_list[0]
    y_tile = tile_pixel_list[1]
    x_pixel = tile_pixel_list[2]
    y_pixel = tile_pixel_list[3]
    
    # 緯度経度をひとつの要素にまとめる
    coordinate_list = [str(lat), str(lng)]
    coordinate_str = "/".join(coordinate_list)

    # 各災害情報を取得し、リストに格納
    result_list_kouzui = ['洪水'] + mod.shisui_hazard_level(0, x_tile, y_tile, x_pixel, y_pixel) + [coordinate_str]
    result_list_tsunami = ['津波'] + mod.shisui_hazard_level(1, x_tile, y_tile, x_pixel, y_pixel) + [coordinate_str]
    result_list_takashio = ['高潮'] + mod.shisui_hazard_level(2, x_tile, y_tile, x_pixel, y_pixel) + [coordinate_str]
    result_list_houkai = ['急傾斜地の崩壊'] + mod.dosya_hazard_level(0, x_tile, y_tile, x_pixel, y_pixel) + [coordinate_str]
    result_list_doseki =['土石流'] + mod.dosya_hazard_level(1, x_tile, y_tile, x_pixel, y_pixel) + [coordinate_str]
    result_list_zisuberi = ['地すべり'] + mod.dosya_hazard_level(2, x_tile, y_tile, x_pixel, y_pixel) + [coordinate_str]
    result_list_zishin =  ['地震'] + mod.earthquake_rank(mod.get_earthquake_API(lat,lng))

    # 各災害情報をひとつのリストにまとめる
    lists = []
    lists.append(result_list_kouzui)
    lists.append(result_list_tsunami)
    lists.append(result_list_takashio)
    lists.append(result_list_houkai)
    lists.append(result_list_doseki)
    lists.append(result_list_zisuberi)
    lists.append(result_list_zishin)

    # データフレームに変換して出力
    df = pd.DataFrame(lists)
    df.columns = (['自然災害名称', 'あんしんレベル', 'ハザード情報','詳細情報'])
    
    #ハザードレベル最大値のリストからあんしんレベルのリストとを引いて、レベルを逆にする
    list_hazard_level = df['あんしんレベル'].tolist()
    max_hazard = [6,8,8,3,3,3,4]

    df1 = pd.DataFrame({'max_hazard': max_hazard, 'list_hazard_level': list_hazard_level})
    anshin_list = df1['max_hazard'] - df1['list_hazard_level']

    df['あんしんレベル'] = anshin_list

    #あんしんレベルを％に置き換えた数値をDFに追加
    max_levels = {
    "洪水": 6,
    "津波": 8,
    "高潮": 8,
    "急傾斜地の崩壊": 3,
    "土石流": 3,
    "地すべり": 3,
    "地震": 4
    }
    
    df["パーセンテージ"] = (df["あんしんレベル"] / df["自然災害名称"].map(max_levels)) * 100
    df["パーセンテージ"] = df["パーセンテージ"].round().astype(float)

    #地震の詳細情報のみ％に変換
    df.iloc[6, 3] = str(df.iloc[6, 3]) + '%'

    #地震の詳細情報の小数点第3位を四捨五入
    val = round(float(df.iloc[6, 3].strip('%')) / 100, 3)
    df.iloc[6, 3] = f"{val:.2%}"

    #最も確率の高い震度をハザード情報に追加 震度数:確率％
    new_value = df.iloc[6, 2] + ' : ' + df.iloc[6, 3].replace('%', '') + '%'
    df.at[6,'ハザード情報'] = new_value
    df.at[6,'詳細情報'] = np.nan

    #地震の震度確率リストを/で区切りひとつにまとめ、詳細情報に追加
    shindo_list = mod.get_earthquake_API(lat,lng)
    join_shindo_list = "/".join(str(x) for x in shindo_list)

    df.loc[6,'詳細情報'] = join_shindo_list
    df = df.set_index('自然災害名称')
    # df
    return df

