from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from api.serializers import Place_infoSerializer, Place_keywordsSerializer, Plan_Serializer
from api.models import Place_info, Place_keywords, Plan
import datetime as dt
from django.db.models import Q
import random
from django.http import JsonResponse
import json
from ast import literal_eval

from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from numpy import dot
from numpy.linalg import norm
from operator import itemgetter
import requests
import folium
import pandas as pd
import copy

#공항정보
airport_data = {
    "contentsid": "CNTS_000000000019568",
    "category": "c1",
    "title": "제주국제공항",
    "alltag": "공항,제주국제공항,실내관광지,어트랙션,공용주차장,현금결제,카드결제,화장실,무료 WIFI,흡연구역,편의점,음료대,유도 및 안내시설,경보 및 피난시설,임산부 휴게시설,엘리베이터,단독접근가능,단차없음,청각장애인 접근성,시각장애인 접근성,저상버스 접근 가능,장애인 전용 리프트,장애인 화장실,승강기,장애인 전용 주차장,수동 휠체어 대여 가능,전동 휠체어 대여 가능,테이블 비치,쉬움",
    "tag": "공항,제주국제공항,실내관광지,어트랙션,무장애관광",
    "address": "제주특별자치도 제주시 공항로 2",
    "latitude": 33.5063344,
    "longitude": 126.4952613,
    "thumbnail": "https://api.cdn.visitjeju.net/photomng/thumbnailpath/201804/30/d5f680da-0025-4733-98f3-b802170a3f7b.jpg",
    "kakaoid": "10808261",
    "star": 3.8,
    "starnum": 177
}

#코사인 유사도 구하기
def cosine_similarity(A, B):
    return dot(A, B)/(norm(A)*norm(B))

#두 지점의 거리 계산(km)
def cal_dist(start_latitude,start_longitude, end_latitude,end_longitude):
    return (((float(end_latitude) - float(start_latitude))*88.8)**2 +((float(end_longitude) - float(start_longitude))*88.8)**2)**(1/2)   

#가장 가까운 지점 계산
def near_point(random_place, last_end_latitude, last_end_longitude):
    random_place2 = copy.deepcopy(random_place)
    dist1 = cal_dist(last_end_latitude, last_end_longitude, random_place2[0]["latitude"], random_place2[0]["longitude"])
    while True:
        dist2 = cal_dist(last_end_latitude, last_end_longitude, random_place2[1]["latitude"], random_place2[1]["longitude"])
        if dist1 > dist2:
            del random_place2[0]
            dist1 = dist2
        else:
            del random_place2[1]
        if len(random_place2) < 2:
            break
    selected_place = random_place2[0]
    return selected_place

#이동정보 계산
def navi(last_end_place, selected_place, doc_temp):
    # REST 키
    rest_api_key = 'b160df784ddfc397d6fe91d51bc8d051'
    headers = {"Authorization" : "KakaoAK {}".format(rest_api_key)}
    #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
    url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],selected_place["longitude"], selected_place["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
    # GET을 이용하여 정보 불러오기
    res = requests.get(url, headers=headers)
    # Json 형식으로 불러오기
    #불러온 이동정보를 doc에 추가
    doc_temp = json.loads(res.text)
    
    return doc_temp

def dailyroutemake(sort_place, morining_type, lunch_type, return_airport_type, dinner_type, start_airport_type, start_id, sort_restaurant, sort_accommodation):
    #선택된 장소를 저장할 딕셔너리
    last_end_place = {}

    #api를 통해 얻어온 정보를 저장할 리스트
    doc = []
    doc_temp = []
    
    #정해진 장소 리스트
    choose_list = []
    choose_list_place = []
    last_end_place = {}
    
    # 가중치 설정
    # weight_list = [20]*20 + [10]*40 + [1]*(len(sort_place) - 60)
    w1 = 1 / (3*20)
    w2 = 1 / (3*40)
    w3 = 1 / (3*(len(sort_place) - 60))
    weight_list = [w1]*20 + [w2]*40 + [w3]*(len(sort_place) - 60)
    # 랜덤 선정
    # random_place = random.choices(sort_place, weights=weight_list, k=10)
    random_place_np = np.random.choice(sort_place, 10, replace=False, p=weight_list) #중복방지
    # np.array를 list로
    random_place = random_place_np.tolist()

    # 시작이 공항일때랑 아닐때
    if start_airport_type:
        last_end_place = airport_data
        choose_list.append(last_end_place)
    else:
        first_query_set = Place_info.objects.filter(kakaoid = start_id)
        first_serializer = Place_infoSerializer(first_query_set, many=True)
        first_data = first_serializer.data
        last_end_place = first_data[0]
        choose_list.append(last_end_place)
    
    # 아침장소 선정
    if morining_type == True:
        time_sum = 3 * 3600
        while True:
            selected_place = near_point(random_place, last_end_place["latitude"], last_end_place["longitude"])
            random_place.remove(selected_place)
            sort_place.remove(selected_place)
            #이동정보 생성
            doc_temp = navi(last_end_place, selected_place, doc_temp)
            #이동정보 생성 오류
            if doc_temp["routes"][0]["result_code"] != 0:
                continue
            #업데이트 - 장소버전
            last_end_place = selected_place
            choose_list.append(last_end_place)
            choose_list_place.append(last_end_place)
            doc.append(doc_temp)
            #시간계산 - 반복수체크
            time_sum = time_sum - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
            if time_sum < 0:
                break
    # 점심 식당 선정
    if lunch_type == True:
        n = 0
        while True:
            #식당선정
            selected_restaurant = sort_restaurant[n]
            n = n + 1
            #카페제외
            if "카페" in sort_restaurant[n]["tag"]:
                continue
            #거리계산
            dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], selected_restaurant["latitude"],selected_restaurant["longitude"])
            if dist > 0 and dist < 10:
                sort_restaurant.remove(selected_restaurant)
                #이동정보 생성
                doc_temp = navi(last_end_place, selected_restaurant, doc_temp)
                #이동정보 생성 오류
                if doc_temp["routes"][0]["result_code"] != 0:
                    continue
                #업데이트 - non장소 버전
                last_end_place = selected_restaurant
                choose_list.append(last_end_place)
                doc.append(doc_temp)
                break
    # 오후장소 선정
    time_sum = 5 * 3600
    while True:
        selected_place = near_point(random_place, last_end_place["latitude"], last_end_place["longitude"])
        random_place.remove(selected_place)
        sort_place.remove(selected_place)
        #이동정보 생성
        doc_temp = navi(last_end_place, selected_place, doc_temp)
        #이동정보 생성 오류
        if doc_temp["routes"][0]["result_code"] != 0:
            continue
        #업데이트 - 장소버전
        last_end_place = selected_place
        choose_list.append(last_end_place)
        choose_list_place.append(last_end_place)
        doc.append(doc_temp)
        #시간계산 - 반복수체크
        time_sum = time_sum - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
        if time_sum < 0:
            break
    # 저녁 식당 선정
    if dinner_type == True:
        n = 0
        while True:
            #식당선정
            selected_restaurant = sort_restaurant[n]
            n = n + 1
            #카페제외
            if "카페" in sort_restaurant[n]["tag"]:
                continue
            #거리계산
            dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], selected_restaurant["latitude"],selected_restaurant["longitude"])
            if dist > 0 and dist < 10:
                sort_restaurant.remove(selected_restaurant)
                #이동정보 생성
                doc_temp = navi(last_end_place, selected_restaurant, doc_temp)
                #이동정보 생성 오류
                if doc_temp["routes"][0]["result_code"] != 0:
                    continue
                #업데이트 - non장소 버전
                last_end_place = selected_restaurant
                choose_list.append(last_end_place)
                doc.append(doc_temp)
                break
    # 숙소저장용
    last_id = ""
    end_latitude = ""
    end_longitude = ""
    # 숙박인 경우
    if return_airport_type == False:
        n = 0
        while True:
            #숙소선정
            selected_accommodation = sort_accommodation[n]
            n = n + 1
            #거리계산
            dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], selected_accommodation["latitude"],selected_accommodation["longitude"])
            if dist > 0 and dist < 10:
                sort_accommodation.remove(selected_accommodation)
                #이동정보 생성
                doc_temp = navi(last_end_place, selected_accommodation, doc_temp)
                #이동정보 생성 오류
                if doc_temp["routes"][0]["result_code"] != 0:
                    continue
                #업데이트 - non장소 버전
                last_end_place = selected_accommodation
                choose_list.append(last_end_place)
                doc.append(doc_temp)
                last_id = last_end_place["kakaoid"]
                end_latitude = last_end_place["latitude"]
                end_longitude = last_end_place["longitude"]
                break
    # 공항 돌아가는 경우
    if return_airport_type == True:
        selected_place = airport_data
        doc_temp = navi(last_end_place, selected_place, doc_temp)
        last_end_place = selected_place
        choose_list.append(last_end_place)
        doc.append(doc_temp)

    return sort_place, doc, choose_list, choose_list_place, last_id, end_latitude, end_longitude

# Create your views here.
@csrf_exempt
def Place_info_list(request):
    if request.method == 'GET':
        query_set = Place_info.objects.all()
        serializer = Place_infoSerializer(query_set, many=True)
        return JsonResponse(serializer.data, safe=False)

@csrf_exempt   
def Place_info_view(request, pk):
    Place_obj = Place_info.objects.get(pk = pk)
    if request.method == 'GET':
        serializer = Place_infoSerializer(Place_obj)
        return JsonResponse(serializer.data, safe=False)

@csrf_exempt    
def plan_maker(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        startdate = dt.datetime.strptime(data['startDate'], "%Y. %m. %d.")
        enddate = dt.datetime.strptime(data['endDate'], '%Y. %m. %d.')
        themes = data["themes"]
        with_data = data["with"]
        if with_data == None:
            with_data = ""
        user = ""
        is_first_tag = True
        if "체험" in themes:
            if is_first_tag:
                user += "체험"
            else:
                user += ', ' + "체험"
        if "액티비티" in themes:
            if is_first_tag:
                user += "액티비티"
            else:
                user += ', ' + "액티비티"
        if "자연" in themes:
            if is_first_tag:
                user += "자연"
            else:
                user += ', ' + "자연"
        if "해변" in themes:
            if is_first_tag:
                user += "해변"
            else:
                user += ', ' + "해변"
        if "휴식" in themes:
            if is_first_tag:
                user += "휴식"
            else:
                user += ', ' + "휴식"
        if "포토스팟" in themes:
            if is_first_tag:
                user += "포토스팟"
            else:
                user += ', ' + "포토스팟"
        if "부모님" in with_data:
            if is_first_tag:
                user += "부모님"
            else:
                user += ', ' + "부모님"
        if "아이" in with_data:
            if is_first_tag:
                user += "아이"
            else:
                user += ', ' + "아이"
        if "커플" in with_data:
            if is_first_tag:
                user += "커플"
            else:
                user += ', ' + "커플"
        if "친구" in with_data:
            if is_first_tag:
                user += "친구"
            else:
                user += ', ' + "친구"
        
        datenum = (enddate - startdate).days
        
        morining_type = True
        lunch_type = True
        dinner_type = True
        
        #시작시간 받아 오기 
        if data['times']['start'] == "아침":
            morining_type = True
            lunch_type = True
        elif data['times']['start'] == "점심":
            morining_type = False
            lunch_type = True
        elif data['times']['start'] == "오후":
            start_time = 14
            morning_time = 0
            morining_type = False
            lunch_type = False
        
        if data['times']['end'] == "18-20시":
            dinner_type = False
        elif data['times']['end'] == "20-21시":
            dinner_type = True
        elif data['times']['end'] == "21-22시":
            dinner_type = True
        
        #유사도를 추가해 사용할 리스트
        place = []

        #장소들의 태그들을 모두 저장할 리스트
        tag = []
        #모든 장소 불러오기
        c1_query_set = Place_info.objects.filter(category = "c1")
        c1_serializer = Place_infoSerializer(c1_query_set, many=True)
        c1_data = c1_serializer.data
        c1_data_count = len(c1_query_set)
        #모든 장소의 태그들 추가
        for i in range(c1_data_count):
            tag.append(c1_data[i]["tag"])
        
        #마지막에 유저 태그 추가
        tag.append(user)

        #태그 벡터화(코사인 유사도를 구하기 위해)
        tfidf_vect_place = CountVectorizer()
        place_vector = tfidf_vect_place.fit_transform(tag)

        place_vector_dense = place_vector.todense()

        #장소별 태그와 유저 태그 비교 (코사인 유사도 이용)
        for j in range(c1_data_count):
            place_vector = np.array(place_vector_dense[j]).reshape(-1,)
            user_vec = np.array(place_vector_dense[c1_data_count-1]).reshape(-1,)

            similarity_tag = cosine_similarity(place_vector, user_vec)

            #1에 가까울수록 유사함

            #장소별 유사도 추가해 저장  
            place.append(c1_data[j])
            place[j]["distance"] = similarity_tag

        #유사도 높은 순으로 정렬
        sort_place = sorted(place, key=itemgetter('distance'), reverse=True)

        #식당을 저장할 리스트
        restaurant = []
        sort_restaurant = []
        
        #모든 음식점 불러오기
        c4_query_set = Place_info.objects.filter(category = "c4")
        c4_serializer = Place_infoSerializer(c4_query_set, many=True)
        c4_data = c4_serializer.data
        c4_data_count = len(c4_query_set)
        for c4_i in range(c4_data_count):   
            restaurant.append(c4_data[c4_i])
        #평점 높은순 정렬
        sort_restaurant = sorted(restaurant, key=itemgetter("star"), reverse=True)
        
        #숙소를 저장할 리스트
        accommodation = []
        sort_accommodation = []
        
        #모든 숙소 불러오기
        c3_query_set = Place_info.objects.filter(category = "c3")
        c3_serializer = Place_infoSerializer(c3_query_set, many=True)
        c3_data = c3_serializer.data
        c3_data_count = len(c3_query_set)
        
        for c3_i in range(c3_data_count):    
            accommodation.append(c3_data[c3_i])
        #평점 높은순 정렬
        sort_accommodation = sorted(accommodation, key=itemgetter("star"), reverse=True)
        
        response_data = []

        p = 0
        start_latitude = 0.0
        start_longitude = 0.0
        end_latitude = 0.0
        end_longitude = 0.0
        for p in range(0, 3):
            return_airport_type = False
            plan_data = {}
            choose_list_place = []
            choose_list = []
            doc = []
            start_id = ""
            last_id = ""
            #1일차
            start_airport_type = True
            if datenum >= 0:
                #시작은 공항
                start_latitude = 33.5059364682672
                start_longitude = 126.495951277797
                #dailyroutemake(sort_place, morining_type, lunch_type, return_airport_type, dinner_type, start_airport_type, start_id, sort_restaurant, sort_accommodation)
                #return sort_place, doc, choose_list, choose_list_place, last_id, end_latitude, end_longitude
                sort_place, doc, choose_list, choose_list_place, last_id, end_latitude, end_longitude = dailyroutemake(sort_place, morining_type, lunch_type, return_airport_type, dinner_type, start_airport_type, start_id, sort_restaurant, sort_accommodation)
                plan_data["day1"] = doc
                plan_data["day1_preview"] = choose_list_place
                plan_data["day1_items"] = choose_list
            #2일차
            start_airport_type = False
            if datenum >= 1:
                #전날 숙소가 시작
                start_id = last_id
                start_latitude = end_latitude
                start_longitude = end_longitude
                #마지막날이면 공항 돌아가기
                if datenum == 1:
                    return_airport_type = True
                    end_latitude = 33.5059364682672
                    end_longitude = 126.495951277797
                sort_place, doc, choose_list, choose_list_place, last_id, end_latitude, end_longitude = dailyroutemake(sort_place, morining_type, lunch_type, return_airport_type, dinner_type, start_airport_type, start_id, sort_restaurant, sort_accommodation)
                plan_data["day2"] = doc
                plan_data["day2_preview"] = choose_list_place
                plan_data["day2_items"] = choose_list
            #3일차
            if datenum >= 2:
                #전날 숙소가 시작
                start_id = last_id
                start_latitude = end_latitude
                start_longitude = end_longitude
                #마지막날이면 공항 돌아가기
                if datenum == 2:
                    return_airport_type = True
                    end_latitude = 33.5059364682672
                    end_longitude = 126.495951277797
                sort_place, doc, choose_list, choose_list_place, last_id, end_latitude, end_longitude = dailyroutemake(sort_place, morining_type, lunch_type, return_airport_type, dinner_type, start_airport_type, start_id, sort_restaurant, sort_accommodation)
                plan_data["day3"] = doc
                plan_data["day3_preview"] = choose_list_place
                plan_data["day3_items"] = choose_list
                
            response_data.append(plan_data)
            
        response_json = json.dumps(response_data)
        
        with open('route.json', 'w', encoding='utf-8-sig') as json_file:
            json.dump(response_data, json_file, ensure_ascii=False, indent="\t")
        
        return HttpResponse(response_json, content_type='application/json')
       
@csrf_exempt    
def map_maker(request, routenum, daynum):
    json_data = {}
    with open('route.json', 'r', encoding='utf-8-sig') as json_file:
        contents = json_file.read()
        json_data_all = json.loads(contents)
        
        json_data = json_data_all[routenum]
    
    if daynum == 0:
        day = "day1"
        day_item = "day1_items"
    elif daynum == 1:
        day = "day2"
        day_item = "day2_items"
    elif daynum == 2:
        day = "day3"
        day_item = "day3_items"

    #맵 생성
    place_len = len(json_data[day])
    
    # map_start_x = json_data[day][0]["routes"][0]["summary"]["origin"]['x']
    # map_start_y = json_data[day][0]["routes"][0]["summary"]["origin"]['y']
    # for i in range(place_len):
    #     map_start_x += json_data[day][i]["routes"][0]["summary"]["destination"]['x']
    #     map_start_y += json_data[day][i]["routes"][0]["summary"]["destination"]['y']   
    # map_start_x = float(map_start_x)/(place_len+1)
    # map_start_y = float(map_start_y)/(place_len+1)
    # 경로 평균보단 제주도 중앙으로 설정
    map_start_x = 126.53487405879748
    map_start_y = 33.37074351877385
    
    map = folium.Map(location=[map_start_y, map_start_x], zoom_start=10, width=600, height=500)

    #색
    col = ["red","blue","green","purple","orange","white","pink"]
    #마커 부분 수정
    #시작 지점 마커
    origin = json_data[day][0]["routes"][0]["summary"]["origin"]
    popup_name = origin['name']
    folium.Marker(location=[origin['y'], origin['x']], icon=folium.Icon(icon="flag",color="blue",prefix='fa'), tooltip=popup_name).add_to(map)
    #나머지 지점 마커
    for n in range(place_len):
        #저장된 이동정보를 불러와서 마커 추가
        origin = json_data[day][n]["routes"][0]["summary"]["origin"]
        destination = json_data[day][n]["routes"][0]["summary"]["destination"]
    
        popup_name = destination['name']
        
        if n == (place_len-1):
            folium.Marker(location=[destination['y'], destination['x']], icon=folium.Icon(icon="flag-checkered",color="red",prefix='fa'), tooltip=popup_name).add_to(map)
        else:
            icon_num = n + 1
            folium.Marker(location=[destination['y'], destination['x']], icon=folium.Icon(icon="%d" %icon_num,color="green",prefix='fa'), tooltip=popup_name).add_to(map)

        vertexes = []
        #각 이동정보에서 경로를 얻어와 저장
        for road in json_data[day][n]['routes'][0]['sections'][0]['roads']:
            r = road['vertexes']
            for i in range(0, len(r), 2):
                vertexes.append((r[i+1], r[i]))
                
        #경로를 그려줌        
        folium.PolyLine(vertexes, color=col[1]).add_to(map)
        #맵 html로 저장
        map.save("api/templates/map.html")

    if request.method == 'GET':
        return render(request, 'map.html')
