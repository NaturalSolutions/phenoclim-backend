#!/usr/bin/env python
# -*- coding: utf-8 -*-
from easy_thumbnails.files import get_thumbnailer
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
import unicodedata
from django.utils.translation import ugettext_lazy as _
from select2 import fields as select2_fields
import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings
from easy_thumbnails.fields import ThumbnailerImageField

# Create your models here.


#########

def create_thumb(image, size):
    """Returns the image resized to fit inside a box of the given size"""
    image.thumbnail(size, Image.ANTIALIAS)
    temp = StringIO()
    image.save(temp, 'png')
    temp.seek(0)
    return SimpleUploadedFile('temp', temp.read())


def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model

    May be used in a model.save() method.

    """
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old


def get_thumbnail(picture):
    if picture:
        options = {'size': (100, 100)}
        return ".." + get_thumbnailer(picture).get_thumbnail(options).url
    return picture.field.default


#espece
class Species(models.Model):
    name = models.CharField(max_length=100, verbose_name="nom")
    #name_fr = models.CharField(max_length=100, verbose_name="nom")
    description = models.TextField(max_length=500)
    picture = ThumbnailerImageField(upload_to='picture/species',
                                    default='no-img.jpg')

    def save(self, *args, **kwargs):
        # Save this photo instance
        if has_changed(self, 'picture') and self.picture:
            # on va convertir l'image en jpg
            #filename = os.path.splitext(os.path.split(self.picture.name)[-1])[0]
            filename = "%s.png" % unicodedata.normalize('NFD', self.name).lower()
            if(self.picture.file):
                """
                if image.mode not in ('L', 'RGB'):
                    image = image.convert('RGB')
                """
                # d'abord la photo elle-même
                self.picture.save(filename,
                                  self.picture.file,
                                  save=False)
        super(Species, self).save()

    class Meta:
        verbose_name = _("Species")
        verbose_name_plural = _("species")
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def thumbnail(self):
        return get_thumbnail(self.picture)

###########


#zone:
class Area(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    codezone = models.CharField(max_length=20, verbose_name=_("codezone"), blank=True)
    lat = models.FloatField(verbose_name="latitude", default=-1.00)
    lon = models.FloatField(verbose_name="longitude", default=1.00)
    altitude = models.FloatField(verbose_name="altitude", null=True, blank=True)
    remark = models.TextField(max_length=100, verbose_name=_("remark"), blank=True)
    commune = models.CharField(max_length=100, verbose_name=_("city"))
    species = select2_fields.ManyToManyField(Species, blank=True, verbose_name=_("species"))

    class Meta:
        verbose_name = _("Area")
        verbose_name_plural = _("Areas")
        ordering = ['name']

    def __str__(self):
        return "%s" % (self.name)

    def get_data(self):
        results = {}
        for individual in self.individual_set.all():
            results.setdefault(individual.species, [])
            results[individual.species].append(individual)
        return results

    def geojson(self, full=False):
        return {
            "type": "Point",
            "coordinates": [self.lon, self.lat],
            "properties": {
                "object": "area",
                "name": self.name,
                "id": self.id
            }
        }

    def getAllGeojson(self):
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        if(self.lon and self.lat):
            geojson["features"].append(self.geojson())

        for ind in self.individual_set.all():
            geojson["features"].append(ind.geojson())
        return geojson

NATIONALITY_CHOICES = (
    ('france', _('french')),
    ('italie', _('italian')),
)

CATEGORY_CHOICES = (
    ('particulier', _('particulier')),
    ('etablissement_scolaire', _('etablissement_scolaire')),
    ('espace_protege', _('espace_protege')),
    ('association', _('association')),
    ('professionnelle', _('professionnelle')),
    ('centre_decouverte', _('centre_decouverte')),
    ('autre', _('autre')),
)


#observateur
class Observer(models.Model):
    user = models.OneToOneField(User)
    city = models.CharField(max_length=100, verbose_name=_("city"))
    fonction = models.CharField(max_length=70, verbose_name=_("fonction"))
    adresse = models.TextField(max_length=80, verbose_name=_("adresse"))
    codepostal = models.CharField(max_length=20, verbose_name=_("codepostal"))
    nationality = models.CharField(max_length=100,
                                   verbose_name=_("nationality"),
                                   choices=NATIONALITY_CHOICES)
    organism = models.CharField(max_length=150, verbose_name=_("organism"),
                                blank=True)
    category = models.CharField(max_length=80, verbose_name=_("category"),
                                choices=CATEGORY_CHOICES)
    phone = models.CharField(max_length=20, verbose_name=_("phone"))
    mobile = models.CharField(max_length=20, verbose_name=_("mobile"))
    is_crea = models.BooleanField(verbose_name=_("is a crea member ?"),
                                  default=False)
    is_active = models.BooleanField(verbose_name=_("is activated?"),
                                    default=False)
    areas = select2_fields.ManyToManyField(Area, verbose_name=_("Areas"),
                                           blank=True)
    date_inscription = models.DateField(blank=True, null=True,
                                        verbose_name=_("Date joined"),
                                        default=datetime.datetime.now)

    class Meta:
        verbose_name = _("Observer")
        verbose_name_plural = _("Observers")

    def __str__(self):
        return u"%s" % self.user.username

    def __unicode__(self):
        return self.user.username

    def getAllGeojson(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [],
        }
        for area in self.areas.all():
            geojson["features"].append(area.getAllGeojson())
        return geojson

##########


#individu
class Individual(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("name"))
    species = models.ForeignKey(Species, verbose_name=_("Species"))
    area = models.ForeignKey(Area, verbose_name=_("Area"))
    is_dead = models.BooleanField(verbose_name=_("is dead?"), default=False)
    lat = models.FloatField(verbose_name="latitude")
    lon = models.FloatField(verbose_name="longitude")
    altitude = models.FloatField(verbose_name="altitude", null=True, blank=True)
    circonference = models.FloatField(verbose_name="circonference", null=True, blank=True)

    remark = models.CharField(max_length=100, verbose_name=_("remark"), blank=True)

    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")
        ordering = ['species', 'name']

    def __unicode__(self):
        return "%s" % (self.name)

    def __str__(self):
        return "%s" % (self.name)

    def geojson(self, draggable=False):
        filename = settings.MEDIA_URL + get_thumbnail(self.species.picture)
        picture_url = filename
        return {
            "type": "Point",
            "coordinates": [self.lon, self.lat],
            "properties": {
                "object": "individual",
                "name": self.name,
                "id": self.id,
                "draggable": draggable,
                "species": self.species.name,
                "picture": picture_url
            }
        }

    def getAllGeojson(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [],
        }
        if self.lat and self.lon:
            geojson["features"].append(self.geojson(draggable=True))
        geojson["features"].append(self.area.geojson())
        return geojson

    def lastSurvey(self):
        last_survey = self.survey_set.first()
        return last_survey

    def get_tasks(self):
        last_stages = []
        next_stages = []
        date_referer = datetime.date.today()
        previous_date = date_referer + relativedelta(months=-2)
        next_date = date_referer + relativedelta(months=+4)
        for stage in self.species.stage_set.all().filter(is_active=True):
            date_start = datetime.date(next_date.year, stage.month_start, stage.day_start)
            #if (stage.month_start > stage.month_start):
            #    year_start = date_refer.
            date_end = datetime.date(previous_date.year, stage.month_end, stage.day_end)
            if( date_referer <= date_start < next_date ):
                last_stages.append((stage, (date_start, datetime.date(date_start.year, stage.month_end, stage.day_end))))
            if( date_referer >= date_end > previous_date):
                next_stages.append((stage, (datetime.date(date_end.year, stage.month_start, stage.day_start), date_end)))
        print "###################"
        #print "sfsfsfsdfs"
        all_stages = last_stages + next_stages
        all_stages = [ (stage, dates, self.survey_set.filter(stage=stage, date__year=dates[0].year).first()) for (stage, dates) in all_stages ]
        all_stages = sorted(all_stages, key=lambda stage: stage[1][0])
        return all_stages


#enneigement
class Snowing(models.Model):
    area = models.ForeignKey(Area, verbose_name=_("Area"))
    observer = models.ForeignKey(Observer, verbose_name=_("Observer"))
    date = models.DateTimeField(verbose_name=_("date"))
    remark = models.CharField(max_length=100, verbose_name=_("remark"), default="", blank=True)
    height = models.FloatField(verbose_name=_("height"))
    temperature = models.FloatField(verbose_name=_("temperature"), null=True, blank=True)

    class Meta:
        verbose_name = _("Snowing")
        verbose_name_plural = _("Snowings")


#stades
class Stage(models.Model):

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    #name_fr = models.CharField(max_length=100, verbose_name=_("Name"))
    species = models.ForeignKey(Species, verbose_name=_("Species"))
    day_start = models.IntegerField(blank=True, null=True,
                                    verbose_name=_("Start day"))
    month_start = models.IntegerField(blank=True, null=True,
                                      verbose_name=_("Start month"))
    day_end = models.IntegerField(blank=True, null=True,
                                  verbose_name=_("En day"))
    month_end = models.IntegerField(blank=True, null=True,
                                    verbose_name=_("End month"))
    order = models.IntegerField(verbose_name=_("Order"))
    picture_before = ThumbnailerImageField(upload_to='picture/stages',
                                           default='no-img.jpg',
                                           verbose_name=_('Before'))
    picture_current = ThumbnailerImageField(upload_to='pictures/stages',
                                            default='no-img.jpg',
                                            verbose_name=_('Current'))
    picture_after = ThumbnailerImageField(upload_to='pictures/stages',
                                          default='no-img.jpg',
                                          verbose_name=_('After'))
    is_active = models.BooleanField(verbose_name=_("is activated?"),
                                    default=True)

    def thumbnail_before(self):
        return get_thumbnail(self.picture_before)

    def thumbnail_current(self):
        return get_thumbnail(self.picture_current)

    def thumbnail_after(self):
        return get_thumbnail(self.picture_after)

    def __str__(self):
        return u"%s" % self.name

    def __unicode__(self):
        return self.name


#observation
class Survey(models.Model):
    individual = models.ForeignKey(Individual)
    observer = models.ForeignKey(Observer, verbose_name=_("observer"), blank=True, null=True)
    stage = models.ForeignKey(Stage, verbose_name=_("Stage"))

    answer = models.CharField(max_length=300, verbose_name=_("reponse"), blank=True)
    date = models.DateField(verbose_name=_("survey date"))
    remark = models.CharField(max_length=100, verbose_name=_("remark"), blank=True)

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")
        ordering = ["-date"]
