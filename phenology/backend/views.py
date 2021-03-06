#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, generics
from backend import models, serializers as serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend import sampledb


@api_view(['GET'])
def user_settings(request):
    try:
    	models.Observer.objects.get_or_create(user=request.user)
        serializer = serializers.ObserverSerializer(request.user.observer)
        return Response(serializer.data)
    except:
	from traceback import print_exc
        print_exc()
        pass
        return HttpResponse('Observer Not found', status=403)


@api_view(['GET', 'POST', 'PUT'])
def user_surveys(request):
    areas = models.Area.objects.filter(observer__user=request.user)
    surveys = models.Survey.objects.filter(individual__area=areas)
    serializer = serializers.SurveySerializer(surveys)
    return Response(serializer.data)


class UserSnowCoverList(generics.ListCreateAPIView):
    serializer_class = serializers.SnowingSerializer

    def get_queryset(self):
        user = self.request.user
        return models.Snowing.objects.filter(observer__user=user)

    def pre_save(self, obj):
        """
        Set the object's owner, based on the incoming request.
        """
        obj.observer = self.request.user.observer
        obj.app_name = self.request.META.get("HTTP_APP_NAME")


class SnowCoverDetail(generics.RetrieveUpdateDestroyAPIView):
    model = models.Snowing
    serializer_class = serializers.SnowingSerializer

    def pre_save(self, obj):
        """
        Set the object's owner, based on the incoming request.
        """
        obj.observer = self.request.user.observer


class UserSurveyList(generics.ListCreateAPIView):
    serializer_class = serializers.SurveySerializer

    def get_queryset(self):
        user = self.request.user
        areas = models.Area.objects.filter(observer__user=user)
        surveys = models.Survey.objects.filter(individual__area=areas)
        return surveys

    def pre_save(self, obj):
        """
        Set the object's owner, based on the incoming request.
        """
        obj.observer = self.request.user.observer
        obj.app_name = self.request.META.get("HTTP_APP_NAME", "")


class SurveyDetail(generics.RetrieveUpdateDestroyAPIView):
    model = models.Survey
    serializer_class = serializers.SurveySerializer

    def pre_save(self, obj):
        """
        Set the object's owner, based on the incoming request.
        """
        obj.observer = self.request.user.observer


def create_sample(request):
    sampledb.create_sample_data()
    return HttpResponse("done")


#@api_view(['GET'])
class ObserverViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows areas to be viewed or edited.
    """
    serializer_class = serializers.ObserverSerializer
    model = models.Observer


class AreaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows areas to be viewed or edited.
    """
    model = models.Area


class IndividualViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows areas to be viewed or edited.
    """
    serializer_class = serializers.IndividualSerializer
    model = models.Individual


class SpeciesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows areas to be viewed or edited.
    """
    serializer_class = serializers.SpeciesSerializer
    model = models.Species


class SurveyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows areas to be viewed or edited.
    """
    serializer_class = serializers.SurveySerializer
    model = models.Survey
