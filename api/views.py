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

#코사인 유사도 구하기
def cosine_similarity(A, B):
    return dot(A, B)/(norm(A)*norm(B))

#두 지점의 거리 계산(km)
def cal_dist(start_latitude,start_longitude, end_latitude,end_longitude):
    return (((float(end_latitude) - float(start_latitude))*88.8)**2 +((float(end_longitude) - float(start_longitude))*88.8)**2)**(1/2)   

def dailyroutemake(sort_place, start_longitude, start_latitude, morining_type, lunch_type, night_type, dinner_type, return_airport_type, start_airport_type, start_time, morning_time, end_longitude, end_latitude, start_id):
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
    #장소전체는 저장하고 유사도 50으로 바꿈
    #장소 중복을 피하기 위해 
    sort2_place = sort_place[:50]
    
    #선택된 장소를 저장할 딕셔너리
    end_place = {}
    last_end_place = {}
    
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

    #정해진 장소 리스트
    choose_list = []
    choose_list_place = []
    
    #api를 통해 얻어온 정보를 저장할 리스트
    doc = []
    doc_temp = []
    
    # REST 키
    rest_api_key = 'b160df784ddfc397d6fe91d51bc8d051'
    headers = {"Authorization" : "KakaoAK {}".format(rest_api_key)}
    
    total_time = 0
    #첫번째 장소 (점심이 첫번째가 아닐때만)
    #첫번째 장소는 거리 상관없이 랜덤
    if ((morining_type == True) and (lunch_type == True)) or ((morining_type == False) and (lunch_type == False)): 
        while True:
            random_num = random.randint(0,49)
            #시작은 거리 상관없이 랜덤하게 상위 50개중에서
            end_place = sort_place[random_num]
            #선택된 장소 저장
            last_end_place = end_place
    
            url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(start_longitude,start_latitude,end_place["longitude"], end_place["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"
            # GET을 이용하여 정보 불러오기
            res = requests.get(url, headers=headers)
            # Json 형식으로 불러오기
            #불러온 이동정보를 doc에 추가
            doc_temp = json.loads(res.text)
            if doc_temp["routes"][0]["result_code"] == 0:
                if start_airport_type:
                    doc_temp["routes"][0]["summary"]["origin"]['name'] = airport_data["title"]
                    choose_list.append(airport_data)
                else:
                    first_query_set = Place_info.objects.filter(kakaoid = start_id)
                    first_serializer = Place_infoSerializer(first_query_set, many=True)
                    first_data = first_serializer.data
                    doc_temp["routes"][0]["summary"]["origin"]['name'] = first_data[0]["title"]
                    choose_list.append(first_data[0])
                doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
                doc.append(doc_temp)
                choose_list.append(last_end_place)
                choose_list_place.append(last_end_place)
                del sort2_place[random_num]
                del sort_place[random_num]
                break
            
        if morining_type == True: 
            morning_time = morning_time - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
        total_time = int(doc_temp["routes"][0]["summary"]["duration"]) + 3600
    
    #오전 일정
    if morining_type == True:
        # 오전 부분 = 오전 시간을 모두 채울 떄까지 진행
        loop_num = 0
        last_num = len(sort2_place) - 1
        while True:
            random_num = random.randint(0,last_num)
                 
            if loop_num < 20:
                loop_num += 1
                dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort2_place[random_num]["latitude"],sort2_place[random_num]["longitude"])
                if dist >= 1 and dist <= 15:
                    end_place = sort2_place[random_num]

                    #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
                    url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort2_place[random_num]["longitude"], sort2_place[random_num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
                    # GET을 이용하여 정보 불러오기
                    res = requests.get(url, headers=headers)
                    # Json 형식으로 불러오기
                    #불러온 이동정보를 doc에 추가
                    doc_temp = json.loads(res.text)
                    if doc_temp["routes"][0]["result_code"] != 0:
                        continue  
                      
                    if morning_time - int(json.loads(res.text)["routes"][0]["summary"]["duration"]) - 3600 + 600 < 0:
                        break
                    else:
                        doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
                        last_end_place = end_place
                        morning_time = morning_time - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
                        total_time += int(doc_temp["routes"][0]["summary"]["duration"]) + 3600
                        doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]                       
                        doc.append(doc_temp)
                        choose_list.append(last_end_place)
                        choose_list_place.append(last_end_place)
                        del sort2_place[random_num]
                        del sort_place[random_num]
                        last_num -= 1
                        continue
            #50번 찾아도 없음
            else:
                random_num = random.randint(100,400)
                dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort_place[random_num]["latitude"],sort_place[random_num]["longitude"])
                if dist >= 1 and dist <= 15:
                    end_place = sort_place[random_num]
                            
                    #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
                    url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort_place[random_num]["longitude"], sort_place[random_num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
                    # GET을 이용하여 정보 불러오기
                    res = requests.get(url, headers=headers)
                    # Json 형식으로 불러오기
                    #불러온 이동정보를 doc에 추가
                    doc_temp = json.loads(res.text)
                    if doc_temp["routes"][0]["result_code"] != 0:
                        continue
                    
                    if morning_time - int(json.loads(res.text)["routes"][0]["summary"]["duration"]) - 3600 + 600 < 0:
                        break
                    else:   
                        doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
                        last_end_place = end_place    
                        morning_time = morning_time - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
                        total_time += int(doc_temp["routes"][0]["summary"]["duration"]) + 3600
                        
                        doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
                        doc.append(doc_temp)
                        choose_list.append(last_end_place)
                        choose_list_place.append(last_end_place)

                        del sort_place[random_num]
            
                        continue
    
    #점심 식사
    if lunch_type == True:
        
        #가장 가까운 식당 추천
        n = 0
        num = 0
        min = 20000
        lunch_n_temp = list() #범위내의 레스토랑 후보군
        last_num = len(sort2_place) -1
        #카페는 제거
        while True:
            if n == last_num:
                break
            if "카페" in sort_restaurant[n]["tag"]:
                del sort_restaurant[n]
                last_num -= 1
            else:
                dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort_restaurant[n]["latitude"],sort_restaurant[n]["longitude"])
                if dist >= 1 and dist <= 10:
                    lunch_n_temp.append(n)
                    if dist <= min:
                        min = dist
                        end_place = sort_restaurant[n]
                        num = n
                n += 1
            
        #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
        #점심이 처음이면 시작점은 스타트포인트
        if (morining_type == False) and (lunch_type == False):
            url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(start_longitude,start_latitude,sort_restaurant[num]["longitude"], sort_restaurant[num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
            if start_airport_type:
                doc_temp["routes"][0]["summary"]["origin"]['name'] = airport_data["title"]
                choose_list.append(airport_data)
	    	else:
	        	first_query_set = Place_info.objects.filter(kakaoid = start_id)
                first_serializer = Place_infoSerializer(first_query_set, many=True)
                first_data = first_serializer.data
                doc_temp["routes"][0]["summary"]["origin"]['name'] = first_data[0]["title"]
                choose_list.append(first_data[0])
	    	# GET을 이용하여 정보 불러오기
            res = requests.get(url, headers=headers)
            doc_temp = json.loads(res.text)
	    last_end_place = end_place
	    doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
	    doc.append(doc_temp)
	    del sort_restaurant[num]
	    choose_list.append(last_end_place)
        else:
            url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort_restaurant[num]["longitude"], sort_restaurant[num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
            # GET을 이용하여 정보 불러오기
            res = requests.get(url, headers=headers)
            doc_temp = json.loads(res.text)
            doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
            last_end_place = end_place
            doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
            doc.append(doc_temp)
            del sort_restaurant[num]
            choose_list.append(last_end_place)
            
        total_time += int(doc_temp["routes"][0]["summary"]["duration"]) + 3600     

        
    #오후 일정
    afternoon_time = 0
    if night_type == True:
        afternoon_time = 18 - start_time - (total_time/3600)
    else:
        afternoon_time = 20 - start_time - (total_time/3600)
    afternoon_time = afternoon_time * 3600
    
    loop_num = 0
    last_num = len(sort2_place) - 1
    while True:
        random_num = random.randint(0,last_num)
        
        if loop_num < 20:
            loop_num += 1
            dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort2_place[random_num]["latitude"],sort2_place[random_num]["longitude"])
            if dist >= 1 and dist <= 15:
                end_place = sort2_place[random_num]
                
                #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
                url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort2_place[random_num]["longitude"], sort2_place[random_num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
                # GET을 이용하여 정보 불러오기
                res = requests.get(url, headers=headers)
                # Json 형식으로 불러오기
                #불러온 이동정보를 doc에 추가
                doc_temp = json.loads(res.text)
                if doc_temp["routes"][0]["result_code"] != 0:
                    continue
                
                if afternoon_time - int(json.loads(res.text)["routes"][0]["summary"]["duration"]) - 3600 + 600 < 0:
                    break
                else:
                    afternoon_time = afternoon_time - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
                    total_time += int(doc_temp["routes"][0]["summary"]["duration"]) + 3600
                    doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
                    last_end_place = end_place
                    doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
                    doc.append(doc_temp)
                    choose_list.append(last_end_place)
                    choose_list_place.append(last_end_place)
                    del sort2_place[random_num]
                    del sort_place[random_num]
                    last_num -= 1
                    continue
        #50번 찾아도 없음
        else:
            random_num = random.randint(100,400)
            dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort_place[random_num]["latitude"],sort_place[random_num]["longitude"])
            if dist >= 1 and dist <= 15:
                end_place = sort_place[random_num]            
                        
                #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
                url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort_place[random_num]["longitude"], sort_place[random_num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
                # GET을 이용하여 정보 불러오기
                res = requests.get(url, headers=headers)
                # Json 형식으로 불러오기
                #불러온 이동정보를 doc에 추가
                doc_temp = json.loads(res.text)
                if doc_temp["routes"][0]["result_code"] != 0:
                    continue
                
                if afternoon_time - int(json.loads(res.text)["routes"][0]["summary"]["duration"]) - 3600 + 600 < 0:
                    break
                else:
                    afternoon_time = afternoon_time - int(doc_temp["routes"][0]["summary"]["duration"]) - 3600
                    total_time += int(doc_temp["routes"][0]["summary"]["duration"]) + 3600
                    doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
                    last_end_place = end_place
                    doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
                    doc.append(doc_temp)
                    choose_list.append(last_end_place)
                    choose_list_place.append(last_end_place)

                    del sort_place[random_num]
                    continue

    #저녁 식사        
    if dinner_type == True:
        #가장 가까운 식당 추천
        n = 0
        num = 0
        min = 20000
        dinner_n_temp = list() #범위내의 레스토랑 후보군
        
        last_num = len(sort_restaurant) - 1
        #카페는 제거
        while True:
            if n == last_num:
                break
            if "카페" in sort_restaurant[n]["tag"]:
                del sort_restaurant[n]
                last_num -= 1
            else:
                dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort_restaurant[n]["latitude"],sort_restaurant[n]["longitude"])
                if dist >= 1 and dist <= 10:
                    dinner_n_temp.append(n)
                    if dist <= min:
                        min = dist
                        end_place = sort_restaurant[n]
                        num = n
                n += 1
                
        #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
        url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort_restaurant[num]["longitude"], sort_restaurant[num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
        # GET을 이용하여 정보 불러오기
        res = requests.get(url, headers=headers)
        doc_temp = json.loads(res.text)
        doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
        last_end_place = end_place
        doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
        doc.append(doc_temp)
        del sort_restaurant[num]
        choose_list.append(last_end_place)
            
        total_time += int(doc_temp["routes"][0]["summary"]["duration"]) + 3600     
    
        
    if return_airport_type:
        #마지막날 공항가는 경우
        url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],end_longitude,end_latitude) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
        # GET을 이용하여 정보 불러오기
        res = requests.get(url, headers=headers)
        doc_temp = json.loads(res.text) #추가
        doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
        doc_temp["routes"][0]["summary"]["destination"]['name'] = "제주국제공항"
        doc.append(doc_temp)

        choose_list.append(airport_data)
        last_id = ""
        
    else:
        #숙소 (공항돌아가기 X)
        #가장 가까운 숙소 추천
        n = 0
        num = 0
        min = 20000
        accommodation_n_temp = list() #범위내의 숙소 후보군
        for n in range(len(sort_accommodation)):
            dist = cal_dist(last_end_place["latitude"], last_end_place["longitude"], sort_accommodation[n]["latitude"],sort_accommodation[n]["longitude"])
            if dist >= 1 and dist <= 10:
                accommodation_n_temp.append(n)
                if dist <= min:
                    min = dist
                    end_place = sort_accommodation[n]
                    num = n
                
        #마지막으로 이동했던 장소와 다음 이동할 장소의 이동정보 url
        url = "https://apis-navi.kakaomobility.com/v1/directions?origin={0},{1}&destination={2},{3}".format(last_end_place["longitude"],last_end_place["latitude"],sort_accommodation[num]["longitude"], sort_accommodation[num]["latitude"]) + "&waypoints=&priority=RECOMMEND&car_fuel=GASOLINE&car_hipass=false&alternatives=false&road_details=false"            
        # GET을 이용하여 정보 불러오기
        res = requests.get(url, headers=headers)
        doc_temp = json.loads(res.text)
        doc_temp["routes"][0]["summary"]["origin"]['name'] = last_end_place["title"]
        last_end_place = end_place
        doc_temp["routes"][0]["summary"]["destination"]['name'] = last_end_place["title"]
        doc.append(doc_temp)
        del sort_accommodation[num]
        choose_list.append(last_end_place)
        end_longitude = last_end_place["longitude"]
        end_latitude = last_end_place["latitude"]
        last_id = last_end_place["kakaoid"]
        
    return sort_place, doc, end_longitude, end_latitude, choose_list, choose_list_place, last_id
    
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
        
        lunch_time = 12
        morining_time = 0
        start_time = 0
        total_time = 0
        morining_type = True
        lunch_type = True
        night_type = True
        dinner_type = True
        return_airport_type = False

        #시작시간 받아 오기 
        if data['times']['start'] == "아침":
            start_time = 9
            morning_time = (lunch_time - start_time) * 3600
            morining_type = True
            lunch_type = True
        elif data['times']['start'] == "점심":
            start_time = 12
            morning_time = 0
            morining_type = False
            lunch_type = True
        elif data['times']['start'] == "오후":
            start_time = 14
            morning_time = 0
            morining_type = False
            lunch_type = False
        
        if data['times']['end'] == "18-20시":
            night_type = False
            dinner_type = False
        elif data['times']['end'] == "20-21시":
            night_type = False
            dinner_type = True
        elif data['times']['end'] == "21-22시":
            night_type = True
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
            choose_list_all = []
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
                #def dailyroutemake(sort_place, start_longitude, start_latitude, morining_type, lunch_type, night_type, dinner_type, return_airport_type, start_airport_type, start_time, morning_time, end_longitude, end_latitude, start_id)
                sort_place, doc, end_longitude, end_latitude, choose_list, choose_list_place, last_id = dailyroutemake(sort_place, start_longitude, start_latitude, morining_type, lunch_type, night_type, dinner_type, return_airport_type, start_airport_type, start_time, morning_time, end_longitude, end_latitude, start_id)
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
                sort_place, doc, end_longitude, end_latitude, choose_list, choose_list_place, last_id = dailyroutemake(sort_place, start_longitude, start_latitude, morining_type, lunch_type, night_type, dinner_type, return_airport_type, start_airport_type, start_time, morning_time, end_longitude, end_latitude, start_id)
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
                sort_place, doc, end_longitude, end_latitude, choose_list, choose_list_place, last_id = dailyroutemake(sort_place, start_longitude, start_latitude, morining_type, lunch_type, night_type, dinner_type, return_airport_type, start_airport_type, start_time, morning_time, end_longitude, end_latitude, start_id)
                plan_data["day3"] = doc
                plan_data["day3_preview"] = choose_list_place
                plan_data["day3_items"] = choose_list
            
            # new_Plan = Plan()
            # new_Plan.Planid = p
            # new_Plan.Plandata = plan_data
            # new_Plan.save()
                
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
