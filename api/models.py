from django.db import models

# Create your models here.
class Place_info(models.Model):
    contentsid = models.TextField()
    kakaoid = models.TextField(primary_key=True)
    category = models.TextField()
    title = models.TextField()
    alltag = models.TextField(blank=True, default="")
    tag = models.TextField()
    address = models.TextField()
    latitude = models.TextField()
    longitude = models.TextField()
    thumbnail = models.TextField()
    star = models.TextField()
    starnum = models.TextField()

class Place_keywords(models.Model):
    contentsid = models.TextField()
    kakaoid = models.TextField(primary_key=True)
    category = models.TextField()
    experience = models.IntegerField()
    activity = models.IntegerField()
    nature = models.IntegerField()
    beach = models.IntegerField()
    rest = models.IntegerField()
    photo = models.IntegerField()
    parents = models.IntegerField()
    children = models.IntegerField()
    couples = models.IntegerField()
    friends = models.IntegerField()

class Plan(models.Model):
    Planid = models.IntegerField(primary_key=True)
    Plandata = models.TextField()

# class Plan_detail(models.Model):
#     planid = models.IntegerField()
#     seq = models.IntegerField()
#     kakaoid = models.TextField()