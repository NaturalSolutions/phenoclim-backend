# from django.shortcuts import render
# -*- coding: utf-8 -*-

import datetime
import simplejson as json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import DeleteView
from django.core.urlresolvers import reverse_lazy, reverse
import os
base_path = os.path.join(os.path.dirname(__file__))



from querystring_parser import parser
from .utils import as_workbook
from backend import models
from backoffice.forms import AccountForm, AreaForm, IndividualForm,\
    CreateIndividualForm, SurveyForm, SnowingForm, ResetPasswordForm
from django.db.models import Max, Min
from django.db import connection
from backoffice.utils import MyTimer, json_serial, week_query, year_query
from django.utils.crypto import get_random_string
from django.core import mail
from django.conf import settings
from django.template.loader import render_to_string

SURVEY_SETTINGS = {
    'TYPES_ANSWER': [_('isObserved'), _('isDead'),
                     _('isLost'), _('isNever'), _('isPassed')]
}


@login_required(login_url='login/')
def index(request):
    if(models.Observer.objects.filter(user=request.user).count() > 0 and
       request.user.observer.areas.count() > 0):
        return redirect('my-surveys')
    else:
        return redirect('all-surveys')


def map_all_surveys(request):
    return render_to_response("map_all_surveys.html", {},
                              RequestContext(request))


def map_viz(request):
    return render_to_response("map_viz.html", {},
                              RequestContext(request))


def viz_all_surveys(request):
    return render_to_response("viz_all_surveys.html", {},
                              RequestContext(request))


def map_all_snowings(request):
    return render_to_response("map_all_snowings.html", {},
                              RequestContext(request))


def viz_area_surveys(request):
    areas = models.Area.objects.all().exclude(individual__survey__isnull=True)
    return render_to_response("viz_area_surveys.html", {"areas": areas},
                              RequestContext(request))


def viz_region_surveys(request):
    areas = models.Area.objects.all().values_list('id', 'headline')
    return render_to_response("viz_region_surveys.html", {"areas": areas},
                              RequestContext(request))


def get_area_data(request=None, area_id=None):
    if not area_id:
        area_id = request.GET.get("area_id")
    if not area_id:
        return {}

    area = models.Area.objects.get(id=area_id)
    area_dict = {'lon': area.lon, 'lat': area.lat, 'city': area.commune,
                 'altitude': area.altitude, 'name': area.name, 'species': {},
                 'postalcode': area.postalcode}
    surveys = models.Survey.objects.filter(individual__area=area)\
                    .select_related("individual", "stage",
                                    "individual__species")
    for survey in surveys.all():
        species_dict = area_dict["species"].setdefault(
            survey.individual.species_id, {
                "name": survey.individual.species.name, "values": {}})
        stage_dict = species_dict["values"].setdefault(
            survey.stage_id, {
                "name": survey.stage.name, "values": {}})
        individual_dict = stage_dict["values"].setdefault(survey.individual_id,
                                                          [])
        individual_dict.append({
            "year": survey.date.year,
            "date": survey.date})
    if request:
        return HttpResponse(json.dumps(area_dict, default=json_serial),
                            content_type="application/json")
    else:
        return area_dict


def get_data_for_viz(request):
    """ get all amount of surveys per month classified as
        species_id/stage_id/year/month
    """
    results = {}
    cursor = connection.cursor()
    cursor.execute('SELECT ' +
                   year_query() +
                   ' as year,' +
                   week_query() +
                   ' as week, COUNT(*),' +
                   'stage_id , species_id ' +
                   'FROM backend_survey, backend_stage ' +
                   'WHERE backend_survey.stage_id=backend_stage.id ' +
                   'GROUP BY stage_id, year, week, species_id;')
    keys = ['year', 'week', 'count', 'stage_id', 'species_id']
    for survey in cursor.fetchall():
        survey_dict = dict(zip(keys, survey))
        species = results.setdefault(survey_dict["species_id"], {})
        stage = species.setdefault(survey_dict["stage_id"], {})
        year = stage.setdefault(survey_dict["year"], {})
        year[survey_dict["week"]] = int(survey_dict["count"])

    return HttpResponse(json.dumps(results, default=json_serial),
                        content_type="application/json")


def get_species_list(request):
    """ get all species with stages linked
        used to populate combobox
    """
    timer = MyTimer("get_species_list")
    timer.capture()
    cursor = connection.cursor()
    sql = 'SELECT ' + year_query() + ' as year, stage_id, COUNT(*) ' +\
          'FROM backend_survey ' +\
          'GROUP BY year, stage_id;'
    cursor.execute(sql)
    stage_years = {}
    for year, stage_id, count in cursor.fetchall():
        stages = stage_years.setdefault(stage_id, [])
        stages.append({"year": year, "count": count})

    species = [{"id": species.id,
                "label": species.name,
                "stages": [{"id": stage.id,
                            "label": stage.name,
                            "years": stage_years.get(stage.id, []),
                            "order": stage.order}
                           for stage in
                           species.stage_set.all().order_by("order")]}
               for species in models.Species.objects.all().order_by("name")]
    timer.capture()
    print timer.output()
    return HttpResponse(json.dumps(species, default=json_serial),
                        content_type="application/json")


def get_min_max_surveys(stage_id):
    cursor = connection.cursor()
    cursor.execute('SELECT ' + year_query() + ' as year,' +
                   'MAX(date) as max, MIN(date) as min ' +
                   'FROM backend_survey ' +
                   'WHERE stage_id=%s ' % stage_id +
                   'GROUP BY year order by year;')
    results = []
    for survey in cursor.fetchall():
            results.append({"min": survey[2],
                            "max": survey[1],
                            "year": survey[0]
                            })
    return results


def search_surveys(request):
    """ get all individuals
        used to get data for map rendering
        can be filtered by species (species_id)
    """
    observers = models.Observer.objects.all()
    timer = MyTimer()
    cursor = connection.cursor()
    timer.capture()
    classified = {}
    results = {}
    species_id = request.GET.get("species_id")
    notdead = request.GET.get("not_dead")
    individuals = models.Individual.objects.all()
    areas = models.Area.objects.all()
    if species_id and species_id.isdigit():
        individuals = individuals.filter(species__id=species_id)
        areas = areas.filter(individual__species__id=species_id)
        observers = observers.filter(areas__individual__species__id=species_id)

        area_organism = {}
        area_org_sql = "SELECT area_id, observer_id, bo.organism " +\
                       "FROM backend_observer_areas as boa, backend_observer as bo " +\
                       "WHERE boa.observer_id=bo.id"
        cursor.execute(area_org_sql)
        for area_id, observer_id, organism in cursor.fetchall():
            area = area_organism.setdefault(area_id, [])
            if not organism:
                organism = "Particulier"
            area.append(organism)

        classified = {a.id: {'lon': a.lon, 'lat': a.lat, 'city': a.commune,
                             'altitude': a.altitude, 'name': a.name,
                             'id': a.id,
                             'nb_individuals': 0,
                             "organisms": ",".join(area_organism.get(a.id, [])),
                             'values': {}, 'postalcode': a.postalcode}
                      for a in areas}

        for ind in individuals:
            tmp = classified[ind.area_id]
            if (tmp['lat'] == 1 or tmp['lat'] == -1) and\
               (ind.lat != 1 and ind.lat != -1):
                tmp['lat'] = ind.lat
                tmp['lon'] = ind.lon
            tmp['nb_individuals'] += 1

        timer.capture()
        if notdead == 'true' :
            """ 'isObserved' and not with 'en_erreur' status """
            survey_sql = 'SELECT ' + year_query() + ' as year, ' +\
                        ' timestamp without time zone \'1970-01-01\' + cast( avg(EXTRACT(EPOCH FROM date::timestamp))::text as interval) as avg_date, ' +\
                        'COUNT(*), MAX(date), MIN(date), stage_id, species_id, area_id FROM backend_survey, backend_individual ' +\
                        ' WHERE backend_survey.individual_id=backend_individual.id AND ' +\
                        'backend_individual.species_id = %s ' % species_id +\
                        " AND backend_survey.answer ='isObserved' " +\
                        " AND backend_survey.status !='en_erreur' " +\
                        'GROUP BY area_id, species_id, stage_id, year ' +\
                        'ORDER BY area_id, species_id, stage_id,year;'
        else:
            survey_sql = 'SELECT ' + year_query() + ' as year, ' +\
                                'COUNT(*), MAX(date), MIN(date), stage_id, species_id, area_id FROM backend_survey, backend_individual ' +\
                                ' WHERE backend_survey.individual_id=backend_individual.id AND ' +\
                                'backend_individual.species_id = %s ' % species_id +\
                                'GROUP BY area_id, species_id, stage_id, year ' +\
                                'ORDER BY area_id, species_id, stage_id,year;'
        cursor.execute(survey_sql)
        keys = ['year', 'avg_date', 'count', 'max', 'min', 'stage_id',
                'species_id', 'area_id']
        for survey in cursor.fetchall():
            survey_dict = dict(zip(keys, survey))
            area = results.setdefault(survey_dict["area_id"],
                                      classified.get(survey_dict["area_id"]))
            species = area['values'].setdefault(survey_dict["species_id"], {})
            stage = species.setdefault(survey_dict["stage_id"], {})
            stage[survey_dict["year"]] = {
                "avgDate": survey_dict["avg_date"],
                "minDate": survey_dict["min"],
                "maxDate": survey_dict["max"],
                "count": survey_dict["count"],
                "values": {}
            }
        if notdead == 'true' :
            """ 'isObserved' and not with 'en_erreur' status """
            survey_sql = "SELECT " + year_query() + " as year, " + week_query() + " as week, " +\
                        "COUNT(*), stage_id, species_id, area_id FROM backend_survey, backend_individual" +\
                        " WHERE backend_survey.individual_id=backend_individual.id AND " +\
                        "backend_individual.species_id = %s " % species_id +\
                        " AND backend_survey.answer ='isObserved' " +\
                        " AND backend_survey.status !='en_erreur' " +\
                        "GROUP BY area_id, species_id, stage_id, year,  week " +\
                        "ORDER BY area_id, species_id, stage_id,year,week;"
        else:
            """ 'all answer' """
            survey_sql = 'SELECT ' + year_query() + ' as year, ' + week_query() + ' as week, ' +\
                        'COUNT(*), stage_id, species_id, area_id FROM backend_survey, backend_individual ' +\
                        ' WHERE backend_survey.individual_id=backend_individual.id AND ' +\
                        'backend_individual.species_id = %s ' % species_id +\
                        'GROUP BY area_id, species_id, stage_id, year,  week ' +\
                        'ORDER BY area_id, species_id, stage_id,year,week;'
        cursor.execute(survey_sql)
        keys = ['year', 'week', 'count', 'stage_id', 'species_id', 'area_id']
        for survey in cursor.fetchall():
            survey_dict = dict(zip(keys, survey))
            area = classified.get(survey_dict["area_id"])
            species = area['values'].setdefault(survey_dict["species_id"], {})
            stage = species.setdefault(survey_dict["stage_id"], {})
            year = stage.setdefault(survey_dict["year"], {})
            year["values"][survey_dict["week"]] = survey_dict["count"]

        timer.capture()
        print timer.output()

    return HttpResponse(json.dumps(classified, default=json_serial),
                        content_type="application/json")


def get_area_snowings(request):
    """ get all individuals
        used to get data for map rendering
        can be filtered by species (species_id)
    """
    area_id = request.GET.get("area_id")
    classified = {}

    if area_id and area_id.isdigit():
        area = models.Area.objects.get(id=area_id)

        if area:
            snowings = list(area.snowing_set.all().
                            filter(height__gt=0).
                            filter(height__lt=999).
                            values("height", "date"))
            timer = MyTimer()
            # cursor = connection.cursor()
            timer.capture()
            max_height = 1
            if snowings:
                max_height = max([float(s["height"]) for s in snowings])

            classified = {"id": area_id,
                          "maxHeight": max_height,
                          "name": area.name,
                          "altitude": area.altitude,
                          "snowings": snowings
                          }
            timer.capture()
            print timer.output()

    return HttpResponse(json.dumps(classified, use_decimal=True,
                                   default=json_serial),
                        content_type="application/json")


def search_snowings(request):
    """ get all individuals
        used to get data for map rendering
        can be filtered by species (species_id)
    """
    timer = MyTimer()
    cursor = connection.cursor()
    timer.capture()
    classified = {}

    areas = models.Area.objects.all()

    area_organism = {}
    area_org_sql = "SELECT area_id, observer_id, bo.organism " +\
                   "FROM backend_observer_areas as boa, backend_observer as bo " +\
                   "WHERE boa.observer_id=bo.id"
    cursor.execute(area_org_sql)
    for area_id, observer_id, organism in cursor.fetchall():
        area = area_organism.setdefault(area_id, [])
        if not organism:
            organism = "Particulier"
        area.append(organism)

    classified = {a.id: {'lon': a.lon, 'lat': a.lat, 'city': a.commune,
                         'altitude': a.altitude, 'name': a.name,
                         'nb_individuals': 0,
                         'organisms': ','.join(area_organism.get(a.id, [])),
                         'values': {}, 'postalcode': a.postalcode}
                  for a in areas}

    timer.capture()
    snowing_sql = 'SELECT ' + year_query() + ' as year,  area_id, MAX(height) ' +\
                  'FROM backend_snowing ' +\
                  'WHERE height < 999  AND height > 0 ' +\
                  'GROUP BY area_id, year ' +\
                  'ORDER BY area_id, year;'
    cursor.execute(snowing_sql)
    keys = ['year', 'area_id', 'height']
    for snowing in cursor.fetchall():
        snowing_dict = dict(zip(keys, snowing))
        area = classified.get(snowing_dict["area_id"])
        area['values'][snowing_dict["year"]] = snowing_dict["height"]

    timer.capture()
    print timer.output()

    return HttpResponse(json.dumps(classified,
                                   use_decimal=True,
                                   default=json_serial),
                        content_type="application/json")


def export_surveys(request):
    columns = ['stage', 'date', 'individual.species', 'individual', 'individual.area',
               'individual.area.commune', 'answer', 'observer.user.id']
    workbook = None
    if(request.GET.get("id")):
        observer = models.Observer.objects.get(id=int(request.GET.get("id")))
    else:
        if not request.user.observer:
            request.user.observer = models.Observer()
            request.user.save()
        observer = request.user.observer
    queryset = models.Survey.objects.\
        filter(individual__area__observer=observer).all()
    years = queryset.aggregate(Min('date'), Max('date'))
    if years['date__min'] and years['date__max']:
        min_year = years["date__min"].year
        max_year = years["date__max"].year
        for year in range(min_year, max_year + 1):
            queryset_tmp = queryset.filter(date__year=year)
            workbook = as_workbook(queryset_tmp, columns, workbook=workbook, sheet_name=str(year))
    else:
        workbook = as_workbook(queryset, columns, workbook=workbook, sheet_name=str(datetime.date.today().year))
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="export.xls"'
    workbook.save(response)
    return response


def export_snowings(request):
    ''' Function to export all snowings from an observer
        (current observer by default)
    '''
    columns = ['area', 'area.commune', 'date', 'remark', 'height', 'observer.user.id']
    workbook = None
    if(request.GET.get("id")):
        observer = models.Observer.objects.get(id=int(request.GET.get("id")))
    else:
        observer = request.user.observer
    queryset = models.Snowing.objects. \
        filter(observer=observer).all()
    years = queryset.aggregate(Min('date'), Max('date'))
    if years['date__min'] and years['date__max']:
        min_year = years["date__min"].year
        max_year = years["date__max"].year
        for year in range(min_year, max_year + 1):
            queryset_tmp = queryset.filter(date__year=year)
            workbook = as_workbook(queryset_tmp, columns, workbook=workbook, sheet_name=str(year))
    else:
        workbook = as_workbook(queryset, columns, workbook=workbook, sheet_name=str(datetime.date.today().year))
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="export.xls"'
    workbook.save(response)
    return response


##########
# AREA
##########

@login_required(login_url='login/')
def area_detail(request, area_id=-1):
    area = models.Area.objects.filter(id=area_id).first()
    if not area:
        area = models.Area()
        existed = request.user.observer.areas.first()
        if(existed):
            area.lat = existed.lat
            area.lon = existed.lon
            area.region = existed.region
            area.departement = existed.departement
            area.commune = existed.commune
            area.altitude = existed.altitude
            area.postalcode = existed.postalcode
        area.observer = request.user.observer

    if area_id == -1 or request.user.observer in area.observer_set.all():
        if request.POST:
            form = AreaForm(request.POST, instance=area)
            if form.is_valid():
                messages.add_message(request,
                                     messages.SUCCESS,
                                     _('Form is successifully updated'))
                form.save()
                form.instance.observer_set.add(request.user.observer)
                return redirect('area-detail', area_id=form.instance.id)
        else:
            form = AreaForm(instance=area)
        return render_to_response("profile_area.html", {
            "form": form,
        }, RequestContext(request))
    else:
        return redirect(index)


########
# INDIVIDUAL
########

@login_required(login_url='login/')
def individual_detail(request, ind_id=-1):
    individual = models.Individual.objects.filter(id=ind_id).first()
    if not individual:
        individual = models.Individual()
        area_id = request.GET.get("area_id")
        area = models.Area.objects.get(id=area_id)
        nb_ind = area.individual_set.count()
        individual.name = "individu %s" % (nb_ind + 1)
        individual.area = area
        individual.lat = area.lat
        individual.lon = area.lon
    surveys = sorted(individual.survey_set.all(),
                     key=lambda survey: survey.date,
                     reverse=True)
    surveys = surveys[:8]

    if individual.id:
        if request.user.observer in individual.area.observer_set.all():
            if request.POST:
                form = IndividualForm(request.POST, instance=individual)
                if form.is_valid():
                    messages.add_message(request,
                                         messages.SUCCESS,
                                         _('Form is successifully updated'))
                    form.save()
            else:
                form = IndividualForm(instance=individual)
        else:
            messages.add_message(request,
                                 messages.WARNING,
                                 _('Your are not allowed to see this form'))
            return redirect(index)
    else:
        if request.POST:
            form = CreateIndividualForm(request.POST, instance=individual)
            if form.is_valid():
                messages.add_message(request,
                                     messages.SUCCESS,
                                     _('Form is successifully updated'))
                form.save()
                return redirect('individual-detail', ind_id=form.instance.id)

        else:
            form = CreateIndividualForm(instance=individual)

    return render_to_response("profile_individual.html", {
        "form": form,
    }, RequestContext(request))


#######
# SURVEY
#######

@login_required(login_url='login/')
def survey_detail(request, survey_id=-1):
    survey = models.Survey.objects.filter(id=survey_id).first()
    if not survey:
        survey = models.Survey()
        ind_id = request.GET.get("ind_id")
        individual = models.Individual.objects.get(id=ind_id)
        if individual:
            survey.individual = individual
            survey.date = datetime.date.today()
            # TODO : improve how we get stage
            stage = models.Stage.objects.get(id=request.GET.get("stage_id"))
            if not stage:
                stage = individual.species.stage_set.\
                    filter(is_active=True).all().first()
            survey.stage = stage

    if request.POST:
        ind_id = request.POST.get("individual")
        form = SurveyForm(request.POST,
                          instance=survey)

        if form.is_valid():
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
            return redirect(reverse('my-surveys', kwargs={}) + '#' + ind_id )
        else:
            messages.add_message(request,
                                 messages.ERROR,
                                form.errors)
    else:
        form = SurveyForm(instance=survey)
    return render_to_response("survey.html", {
        "form": form,
    }, RequestContext(request))


#######
# SWOWCOVER/SNOWING FEATURE
#######

@login_required(login_url='login/')
def snowing_detail(request, area_id, snowing_id=-1):
    timer = MyTimer()
    timer.capture()
    snowing = models.Snowing.objects.filter(id=snowing_id).first()
    snowings = []

    if not snowing:
        area = models.Area.objects.get(id=area_id)
        snowing = models.Snowing()
        if area:
            snowing.observer = request.user.observer
            snowing.area = area
            snowing.date = datetime.date.today()
    timer.capture()
    if request.POST:
        snowing.observer = request.user.observer
        form = SnowingForm(request.POST,
                           instance=snowing)
        if form.is_valid():
            if snowing.id is None:
                try:
                    snowing = models.Snowing.objects.get(
                        observer=request.user.observer,
                        date=form.cleaned_data['date'],
                        area=snowing.area
                    )
                    form = SnowingForm(request.POST, instance=snowing)
                except ObjectDoesNotExist:
                    pass
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
            return redirect('snowing-detail', area_id=form.instance.area.id)
        else:
            print form.errors
    else:
        form = SnowingForm(instance=snowing)
    timer.capture()
    query = models.Snowing.objects.all().filter(area=snowing.area.id)
    if(snowing.id):
        query = query.exclude(id=snowing.id)
    snowings = [{"date": s.date.strftime("%Y-%m-%d"),
                 "id": s.id,
                 "height": s.height}
                for s in query]
    timer.capture()
    print timer.output()

    lasts_inputs = models.Snowing.objects.filter(observer=request.user.observer)[:10]

    return render_to_response("snowing.html", {
        "form": form,
        "snowings": snowings,
        "last_five": lasts_inputs,
        "area_id": area_id,
    }, RequestContext(request))


#####
# EDIT PROFILE
#####

@login_required(login_url='login/')
def user_detail(request):
    # print request.user
    models.Observer.objects.get_or_create(user=request.user)
    # print request.user.observer
    if not request.user.observer:
        request.user.observer = models.Observer()
        request.user.save()
    if request.POST:
        form = AccountForm(request.POST,
                           instance=request.user.observer)
        if form.is_valid():
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
        else:
            print form.errors
    else:
        form = AccountForm(instance=request.user.observer)

    return render_to_response("profile.html", {
        "form": form,
    }, RequestContext(request))


#######
# REGISTER USER
#######

def register_user(request):
    if request.user and request.user.username:
        return redirect(index)

    if request.POST:
        form = AccountForm(request.POST)
        if form.is_valid():
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Form is successifully updated'))
            form.save()
            user = form.uf.instance

            # Random passord
            password = get_random_string()
            user.set_password(password)
            user.save()
            message = render_to_string('registration_email.html',
                                       {'user': user,
                                        'password': password})
            mail.send_mail(
                subject=ugettext(u"Welcome on Phenoclim website"),
                message=message,
                from_email=settings.FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False)

            return render_to_response("registration_done.html", {
                "form": form,
            }, RequestContext(request))
        else:
            print form.errors
    else:
        instance = models.Observer()
        instance.user = User()
        form = AccountForm(instance=instance)

    return render_to_response("generic_form.html", {
        "form": form,
    }, RequestContext(request))


#######
# PASSWORD RESET FEATURE
#######

def password_reset(request):
    template = "password_new_form.html"
    if request.POST:
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            email = form.data["email"]
            password = get_random_string()
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(password)
                message = render_to_string('password_new_email.html',
                                           {'user': user,
                                            'password': password})
                user.save()
                mail.send_mail(
                    subject=u"%s Phénoclim" % ugettext(u"New password"),
                    message=message,
                    from_email=settings.FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False)

                template = "password_new_done.html"
    else:
        form = ResetPasswordForm()
    return render_to_response(template, {
        "form": form
    }, RequestContext(request))


#####
# MY SURVEYS
#####

@login_required(login_url='login/')
def dashboard(request):
    areas = {a.id: get_area_data(None, a.id) for a in request.user.observer.areas.all()}

    if models.Observer.objects.filter(user=request.user).count > 0:
        return render_to_response("my_surveys.html",
                                  {
                                      "areas": areas
                                  },
                                  RequestContext(request))
    elif request.user.is_staff or request.user.is_superuser:
        return redirect('../admin/')
    else:
        return redirect('allsurveys')
    return render_to_response("base.html", RequestContext(request))


######
# VIZ ALL SURVEYS VIEW
######

@login_required(login_url='login/')
def all_surveys(request):
    surveys = models.Survey.objects.all()[:100]
    return render_to_response("all_surveys.html", {
        "surveys": surveys}, RequestContext(request))


######
# MY STUDIES
######

@login_required(login_url='login/')
def my_studies(request):
    form = AccountForm(instance=request.user.observer)
    return render_to_response("my_studies.html", {
        "form": form }, RequestContext(request))


####
# DATATABLE TOOL
####

def get_surveys(request):
    mapping = {
        "id": "id",
        "observer": "observer",
        "date": "date",
        "species": "individual__species__name",
        "individual": "individual__name",
        "organisms": "individual__area__observer__organism",
        "area": "individual__area__name",
        "stage": "stage__name",
        "answer": "answer"
    }
    parsed = parser.parse(request.GET.urlencode().encode("utf8"))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search = unicode(request.GET.get("search[value]", ""))
    draw = request.GET.get("draw", 1)
    query = models.Survey.objects
    if not request.user.is_staff or not request.user.is_superuser:
        query = query.filter(individual__area__observer__user=request.user)
    # If search is empty, do we really need to do this??
    query = query.filter(Q(individual__name__icontains=search)
                         | Q(individual__area__name__icontains=search)
                         | Q(stage__name__icontains=search)
                         | Q(individual__species__name__icontains=search)
                         | Q(individual__area__observer__organism__icontains=search))

    for ord in parsed["order"].values():
        col = parsed["columns"][ord["column"]]["data"]
        query_1 = mapping.get(col, col)
        if ord["dir"] == "desc":
            query_1 = "-" + query_1
        query = query.order_by(query_1)

    # "Search query" add a lot of joins and duplicate rows. Using distinct() is
    # risky but is an optimistic approach: easier than grouping by each
    # columns (which is a better alternative but hard to maintains without
    # tests).
    # https://docs.djangoproject.com/fr/1.8/ref/models/querysets/#django.db.models.query.QuerySet.distinct
    query = query.distinct()
    filtered_total = query.count()
    filtered_data = query.select_related('individual').all()[start:
                                                             start + length]

    response_data = {
        "draw": int(draw),
        "data": [{"id": o.id,
                  "date": str(o.date),
                  "area": o.individual.area.name,
                  "species": o.individual.species.name,
                  "individual": o.individual.name,
                  "organisms": ",".join(set([a.organism
                                            for a in
                                             o.individual.area.
                                             observer_set.all()
                                             if a.organism]
                                            )),
                  "stage": o.stage.name,
                  "answer": ugettext(o.answer),
                  "categorie": ",".join([a.category
                                         for a in
                                         set(o.individual.area.
                                             observer_set.all())]
                                        )
                  }
                 for o in filtered_data],
        "recordsTotal": models.Survey.objects.count(),
        "recordsFiltered": filtered_total
    }
    return HttpResponse(json.dumps(response_data, default=json_serial),
                        content_type="application/json")
from django.db.models import Count


#######
# MAP ALL SNOWINGS
#######

def viz_snowings(request):
    ref_year = request.GET.get("ref_date")
    if ref_year is None:
        query = models.Snowing.objects.filter(height__gt=0).\
            filter(height__lt=999).values("area", "area__postalcode").\
            annotate(count=Count('id'))
    else:
        query = models.Snowing.objects.filter(height__gt=0).\
            filter(height__lt=999).values("area", "area__postalcode").\
            exclude(date__lt=datetime.datetime(int(ref_year), 1, 1)).\
            annotate(count=Count('id'))

    area_ids = {s["area"]: s["area__postalcode"] for s in query
                if int(s["count"]) > 50}

    def compare_postalcode(postalcode):
        if postalcode.isdigit():
            return float(postalcode)
        else:
            return postalcode

    areas = list(models.Area.objects.filter(pk__in=area_ids.keys()))
    areas = sorted(areas, key=lambda a: compare_postalcode(area_ids[a.id]))
    return render_to_response("viz_snowings.html", {"areas": areas},
                              RequestContext(request))


#######
# DELETE VIEWS
#https://ultimatedjango.com/learn-django/lessons/delete-contact-full-lesson/
# TODO permission
#######
class SurveyDelete(DeleteView):
    model = models.Survey
    template_name = base_path + '/templates/survey_confirm_delete.html'
    success_message = _("Survey was deleted successfully.")

    def get_object(self, queryset=None):
        obj = super(SurveyDelete, self).get_object()
        currentSurvey = models.Survey.objects.get(id=obj.id)

        self.survey = currentSurvey
        return obj

    def get_success_url(self):
        return reverse_lazy('my-surveys',)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(SurveyDelete, self).delete(request, *args, **kwargs)

#######
# CHART SURVEYS
#######
@login_required(login_url='login/')
def chart_surveys(request):
    models.Observer.objects.get_or_create(user=request.user)
    areas = {a.id: get_area_data(None, a.id) for a in request.user.observer.areas.all()}
    if models.Observer.objects.filter(user=request.user).count > 0:
        return render_to_response("chart_surveys.html",
                                  {
                                      "areas": areas
                                  },
                                  RequestContext(request))