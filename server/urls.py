"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('plan/', views.plan_maker),
    path('plan', views.plan_maker),
    path('place_info/', views.Place_info_list),
    path('place_info', views.Place_info_list),
    path('place_info/<str:pk>', views.Place_info_view),
    path('place_info/<str:pk>/', views.Place_info_view),
    path('map/<int:routenum>/<int:daynum>', views.map_maker),
    path('map/<int:routenum>/<int:daynum>/', views.map_maker)
]
