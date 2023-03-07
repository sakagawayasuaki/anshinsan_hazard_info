import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import Control_ANSHIN as con
import plotly.graph_objects as go

#アプリタイトル
st.image("アプリタイトルロゴ.png", use_column_width=True)
#アプリの説明
st.caption('本アプリでは、気になる物件の自然災害に対する"あんしん度"が簡単に確認できちゃいます！')


# クエリパラメータ読み込み
params = st.experimental_get_query_params()
# 住所情報の入力
# 入力された値をsession_stateに格納
layout = st.columns(3)
option =[]
municipality=[]
propertyname=[]
for i in range(3):
    with layout[0]: 
        df_todohuken = pd.DataFrame({
            'first column': ['','北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県', '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県', '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県', '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県', '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'],
            })
        # 初期値の設定
        index_option = 0
        # クエリパラメータがある場合、初期値を変更
        if "option" in params:
            if params["option"][i].strip():
                # index_option = int(df_todohuken.index[(df_todohuken['first column'] == params["option"][i])])
                index_option = int(df_todohuken[df_todohuken['first column']==params["option"][i]].index[0])
        option.append(st.selectbox('({})都道府県'.format(i+1), df_todohuken['first column'],index=index_option, key='opt_{}'.format(i)))

    #市区町村テキストボックス
    with layout[1]:
        # 初期値の設定
        value_muni = ""
        # クエリパラメータがある場合、初期値を変更
        if "municipality" in params:
            if params["municipality"][i].strip():
                value_muni = params["municipality"][i]
        municipality.append(st.text_input('({})市区町村以下'.format(i+1),value=value_muni, key='mani_{}'.format(i)))

    #物件名テキストボックス
    with layout[2]:
        # 初期値の設定
        value_prop = ""
        # クエリパラメータがある場合、初期値を変更
        if "propertyname" in params:
            if params["propertyname"][i].strip():
                value_prop = params["propertyname"][i]
        propertyname.append(st.text_input('({})物件名'.format(i+1),value=value_prop, key='prop_{}'.format(i)))

# st.write((option[i]))
# searchボタンが押されたことがあるかの判定
if 'click' not in st.session_state: 
    #calc_valueがsession_stateに追加されていない場合，空のデータフレームでで初期化
	st.session_state.click = False
            
# searchボタンを押したときに値を更新 
search_btn = st.button(label='search')
if search_btn:
    # optionにデータが入っているか確認（物件名にデータが入っているかで判定した方が良い？）
    flag_not_empty = False
    for i in range(0,3):
        if option[i]:
            flag_not_empty =True
    if flag_not_empty:
        # Controlから返されたデータフレームを格納
        st.session_state.df_hazard = pd.DataFrame(data=[],index=['洪水','津波','高潮','急傾斜地の崩壊','土石流','地すべり','地震'])
        st.session_state.radar_list =[]
        st.session_state.latlng_list = []
        st.session_state.jishin_list =[]
        for i in range(0,3):
            # データがある項目のみsearch実行
            if option[i]:
                # Controlの関数を用いてデータ取得
                df = con.get_disaster_info_from_address(option[i] + municipality[i], propertyname[i])
                # テーブル用データフレーム作成
                col_name = "({})".format(i+1) + propertyname[i]
                st.session_state.df_hazard[col_name] = df['ハザード情報']
                # レーダーチャート用リスト作成
                radar_list_tmp =[]
                dosya_radar_value = min(df['パーセンテージ'].iloc[3],df['パーセンテージ'].iloc[4],df['パーセンテージ'].iloc[5])
                for index,row in df.iterrows():
                    if not(index in ["急傾斜地の崩壊","土石流","地すべり"]):
                        radar_list_tmp.append(row['パーセンテージ'])
                    else:
                        if index=="急傾斜地の崩壊":
                            radar_list_tmp.append(dosya_radar_value)
                radar_list_tmp.append(df['パーセンテージ'].iloc[0])
                st.session_state.radar_list.append(radar_list_tmp)
                # ハザードマップ用データフレーム作成
                st.session_state.latlng_list.append(df['詳細情報'].iloc[0].split('/'))
                # 地震の詳細情報用データフレーム作成
                st.session_state.jishin_list.append(df.loc['地震'][2].split('/'))
            else:
                st.session_state.radar_list.append('')
                st.session_state.latlng_list.append('')
                st.session_state.jishin_list.append('')

        st.session_state.click = True

if st.session_state.click:
    #自然災害のハザード情報のデータフレーム表示
    st.write(st.session_state.df_hazard)
    
    #自然災害あんしんレベルレーダーチャートの表示
    # グラフの色
    # https://plotly.com/python/marker-style/
    # グラフの装飾関係参考
    # https://ai-research-collection.com/add_traceupdate_layout/#toc3
    categories = ['洪水','高潮','津波','土砂災害', '地震','洪水']
    fig = go.Figure()
    # ２つ目以降を入力した場合ずれが生じるので修正必要（辞書型で設定するのが良い？, 判例追加したい
    chart_color_list = ['rgb(0,0,255)','rgb(0,255,0)','rgb(255,0,0)']
    line_width_list = [8,4,2]
    for i in range(0,len(st.session_state.radar_list)):
        if st.session_state.radar_list[i]:
            fig.add_trace(go.Scatterpolar(
                r=st.session_state.radar_list[i],
                theta=categories,
                line=dict(width=line_width_list[i],color=chart_color_list[i]), 
                fill='none',
                opacity=0.7,
                name='({})'.format(i+1)+propertyname[i]
            ))
    fig.update_layout(
        # template=None,
        title=dict(text='あんしん度（0~100%で表示）',
                   font=dict(size=20,color='grey'),
                   x=0.25,
                #    y=0.85
                ),
        autosize=True,
        polar=dict(
            radialaxis=dict(
                visible=True,
                showline=False,
                # showgrid=False,
                range=[0, 100]
            )),
        # angularaxis=dict(tickfont=dict(size=30)),
        # showlegend=False
    )
    st.plotly_chart(fig)


    # 地図表示
    # ラジオボタンで表示したい１つの地図/グラフを選択
    hazard_name_list = ['洪水','津波','高潮','急傾斜地の崩壊','土石流','地すべり','地震']
    datail_info = st.radio(label='詳細情報を表示したい自然災害を選択してください',
                    options=hazard_name_list,
                    index=0,
                    horizontal=True,
    )
    # ラジオボタンのチェックに合わせて、表示されるハザードマップを変更
    # 土砂災害はあんしん度:0,1と2,3で表示するURLが変わる
    hazard_url_list = [ "01_flood_l2_shinsuishin_data", # 洪水
                        "04_tsunami_newlegend_data", # 津波
                        "03_hightide_l2_shinsuishin_data", # 高潮
                        "05_kyukeisyachihoukai",   # 急傾斜地の崩壊：危険区域
                        "05_dosekiryukikenkeiryu", # 土石流：危険区域
                        "05_jisuberikikenkasyo"    # 地すべり：危険区域
                        ]
    # 土砂災害の警戒区域、特別警戒区域のURLリスト
    dosya_alert_url_list = [ "05_kyukeishakeikaikuiki", # 急傾斜地の崩壊：警戒区域
                            "05_dosekiryukeikaikuiki", # 土石流：警戒区域
                            "05_jisuberikeikaikuiki"   # 地すべり：警戒区域
                            ]
    # 詳細情報の表示
    # 地震の震度確率分布を棒グラフで表示(※)
    if datail_info == "地震":
        # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Bar.html
        fig_jishin = go.Figure()
        offset_list = [-0.4,-0.25,-0.1]
        chart_line_color_list = ['rgb(0,0,125)','rgb(0,125,0)','rgb(125,0,0)']
        for i in range(0,len(st.session_state.jishin_list)):
            if st.session_state.jishin_list[i]:
                fig_jishin.add_trace(go.Bar(
                    x=["震度4以下", "震度5弱", "震度5強", "震度6弱", "震度6強以上"],
                    y=st.session_state.jishin_list[i],
                    width = 0.6,
                    offset = offset_list[i],
                    marker_color=chart_color_list[i],
                    marker_line_color=chart_line_color_list[i],
                    marker_line_width=1.5,
                    opacity = 0.6,
                    name='({})'.format(i+1)+propertyname[i]
                ))
        fig_jishin.update_layout(
                title=dict(text='今後30年間の震度確率分布（最大ケース）',
                             font=dict(size=20,color='grey'),
                             x=0.2,
                             y=0.85
                          ),
                xaxis=dict(title='震度'),
                yaxis=dict(title='確率[%]'),
                barmode='overlay'
            )
        st.plotly_chart(fig_jishin)
    # ハザードマップ
    else:
        fmap1 = folium.Map(
            location=st.session_state.latlng_list[0],
            tiles = "OpenStreetMap",
            zoom_start = 14, 
            width = 800, height = 800
        )
        # マーカーピンを追加(※)
        icon_color_list = ['blue','green','red']
        for i in range(0,len(st.session_state.latlng_list)):
            if st.session_state.latlng_list[i]:
                lat = st.session_state.latlng_list[i][0]
                lng = st.session_state.latlng_list[i][1]
                folium.Marker((lat, lng), popup=propertyname[i],icon=folium.Icon(color=icon_color_list[i])).add_to(fmap1)
        # ハザードマップ追加
        map_url = hazard_url_list[hazard_name_list.index(datail_info)]
        folium.raster_layers.TileLayer(
            tiles='https://disaportaldata.gsi.go.jp/raster/{url}/{z}/{x}/{y}.png'.format(url=map_url,z="{z}",x="{x}",y="{y}"),
            fmt='image/png',
            attr="hogehoge",
            tms=False,
            overlay=True,
            control=True,
            opacity=0.7
        ).add_to(fmap1)
        # 土砂災害の場合は警戒区域の地図も追加
        if hazard_name_list.index(datail_info) in range(3,6):
            map2_url = dosya_alert_url_list[hazard_name_list.index(datail_info)-3]
            # st.write(map2_url)
            folium.raster_layers.TileLayer(
                tiles='https://disaportaldata.gsi.go.jp/raster/{url}/{z}/{x}/{y}.png'.format(url=map2_url,z="{z}",x="{x}",y="{y}"),
                fmt='image/png',
                attr="hogehoge",
                tms=False,
                overlay=True,
                control=True,
                opacity=0.7
            ).add_to(fmap1)

        folium.LayerControl().add_to(fmap1)
        # 地図情報を表示
        folium_static(fmap1)

    # コピー用のURL表示(※)
    st.write("共有用URL")
    pref=""
    city=""
    propname=""
    for i in range(0,3):
        if option[i]:
            pref+="option="+option[i]+"&"
        else: pref+="option= &"
        if municipality[i]:
            city+="municipality="+municipality[i]+"&"
        else: city+="municipality= &"
        if propertyname[i]:
            propname+="propertyname="+propertyname[i]+"&"
        else: propname+="propertyname= &"
    copy_url = "https://sakagawayasuaki-anshinsan-hazard-info-view-gs5r95.streamlit.app/?{0}{1}{2}".format(pref,city,propname)
    st.code(copy_url, language='cshtml')
# 災害情報一覧
st.write("取得できる災害情報一覧")
# 洪水の浸水深さのハザードリスト作成
kozui_hazard = ['0.1m未満','0.5m未満','0.5~3m','3~5m','5~10m','10~20m','20m以上','','']
tunami_takashio_hazard = ['なし','0.3m未満','0.3~0.5m','0.5~1m','1~3m','3~5m','5~10m','10~20m','20m以上']
kyukeisya_hazard = ["なし","危険箇所","警戒区域","特別警戒区域","","","","",""]
dosekiryu_hazard = ["なし","危険渓流","警戒区域","特別警戒区域","","","","",""]
jisuberi_hazard = ["なし","危険箇所","警戒区域","特別警戒区域","","","","",""]
earthquake_hazard = ["震度4以下", "震度5弱", "震度5強", "震度6弱", "震度6強以上","","","",""]
hazard_name_index = ['洪水：浸水深さ','津波：浸水深さ','高潮：浸水深さ','急傾斜地の崩壊','土石流','地すべり','地震：確率最大震度']
hazard_level =['災害レベル1','災害レベル2','災害レベル3','災害レベル4','災害レベル5','災害レベル6','災害レベル7','災害レベル8','災害レベル9']
# 各災害情報をひとつのリストにまとめる
lists = []
lists.append(kozui_hazard)
lists.append(tunami_takashio_hazard)
lists.append(tunami_takashio_hazard)
lists.append(kyukeisya_hazard)
lists.append(dosekiryu_hazard)
lists.append(jisuberi_hazard)
lists.append(earthquake_hazard)
# データフレームに変換して出力
df_ref = pd.DataFrame(lists,index=hazard_name_index,columns=hazard_level)
st.dataframe(df_ref,width=None)