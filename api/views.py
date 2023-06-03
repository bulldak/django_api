from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from api.serializers import Place_infoSerializer, Place_keywordsSerializer, Plan_detailSerializer, PlanSerializer
from api.models import Place_info, Place_keywords, Plan_detail, Plan
import datetime as dt
from django.db.models import Q
import random
from django.http import JsonResponse
import json

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
def plan_priview(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        startdate = dt.datetime.strptime(data['startDate'], "%Y. %m. %d.")
        enddate = dt.datetime.strptime(data['endDate'], '%Y. %m. %d.')
        themes = data["themes"]
        
        datenum = (enddate - startdate).days
        
        with_data = data["with"]
        if with_data == None:
            with_data = ""
            
        q=Q()
        q &= Q(category = "c1")
        if "체험" in themes:
            q &= Q(experience = 1)
        if "액티비티" in themes:
            q &= Q(activity = 1)
        if "자연" in themes:
            q &= Q(nature = 1)
        if "해변" in themes:
            q &= Q(beach = 1)
        if "휴식" in themes:
            q &= Q(rest = 1)
        if "포토스팟" in themes:
            q &= Q(photo = 1)
        if "부모님" in with_data:
            q &= Q(parents = 1)
        if "아이" in with_data:
            q &= Q(children = 1)
        if "커플" in with_data:
            q &= Q(couples = 1)
        if "친구" in with_data:
            q &= Q(friends = 1)
        
        placefilter = Place_keywords.objects.filter(q)
        placefilter_all = Place_keywords.objects.filter(category = "c1")
        placefilter_count = len(placefilter)
        placefilter_count_all = len(placefilter_all)
        
        response_data = {
            "plan": []
        }
        for p in range(0, 3):
            
            placelist = []
            for i in range(0, (datenum+1)*3):
                while True:
                    if placefilter_count > i:
                        place = placefilter[random.randrange(0,placefilter_count)].kakaoid
                    else:
                        place = placefilter_all[random.randrange(0,placefilter_count_all)].kakaoid
                    
                    if place in placelist:
                        continue
                    else:
                        placelist.append(place)
                        break
                    
            response_data["plan"].append(placelist)
            
       
                 
        response_json = json.dumps(response_data)
        return HttpResponse(response_json, content_type='application/json')
    


   

        
        
    
        
