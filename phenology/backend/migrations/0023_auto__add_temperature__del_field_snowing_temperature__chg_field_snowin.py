# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Temperature'
        db.create_table(u'backend_temperature', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('select2.fields.ForeignKey')(to=orm['backend.Area'], search_field='name')),
            ('observer', self.gf('select2.fields.ForeignKey')(to=orm['backend.Observer'], search_field='')),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('remark', self.gf('django.db.models.fields.TextField')(default='', max_length=100, blank=True)),
            ('temperature', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'backend', ['Temperature'])

        # Deleting field 'Snowing.temperature'
        db.delete_column(u'backend_snowing', 'temperature')


        # Changing field 'Snowing.observer'
        db.alter_column(u'backend_snowing', 'observer_id', self.gf('select2.fields.ForeignKey')(to=orm['backend.Observer'], search_field=''))

    def backwards(self, orm):
        # Deleting model 'Temperature'
        db.delete_table(u'backend_temperature')

        # Adding field 'Snowing.temperature'
        db.add_column(u'backend_snowing', 'temperature',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'Snowing.observer'
        db.alter_column(u'backend_snowing', 'observer_id', self.gf('select2.fields.ForeignKey')(to=orm['backend.Observer'], search_field='user'))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'backend.area': {
            'Meta': {'object_name': 'Area'},
            'altitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'codezone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'commune': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'departement': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'default': '-1.0'}),
            'lon': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'postalcode': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'region': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'remark': ('django.db.models.fields.TextField', [], {'max_length': '100', 'blank': 'True'}),
            'species': ('select2.fields.ManyToManyField', [], {'to': u"orm['backend.Species']", 'symmetrical': 'False', 'search_field': 'None', 'blank': 'True'})
        },
        u'backend.individual': {
            'Meta': {'object_name': 'Individual'},
            'altitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backend.Area']"}),
            'circonference': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'exposition': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'milieu': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'pente': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'remark': ('django.db.models.fields.TextField', [], {'max_length': '100', 'blank': 'True'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backend.Species']"})
        },
        u'backend.observer': {
            'Meta': {'ordering': "('user__username',)", 'object_name': 'Observer'},
            'adresse': ('django.db.models.fields.TextField', [], {'max_length': '80'}),
            'areas': ('select2.fields.ManyToManyField', [], {'to': u"orm['backend.Area']", 'symmetrical': 'False', 'search_field': 'None', 'blank': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'codepostal': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'date_inscription': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'null': 'True', 'blank': 'True'}),
            'fonction': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_crea': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'nationality': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'organism': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'backend.snowing': {
            'Meta': {'object_name': 'Snowing'},
            'area': ('select2.fields.ForeignKey', [], {'to': u"orm['backend.Area']", 'search_field': "'name'"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'height': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'observer': ('select2.fields.ForeignKey', [], {'to': u"orm['backend.Observer']", 'search_field': "''"}),
            'remark': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '100', 'blank': 'True'})
        },
        u'backend.species': {
            'Meta': {'object_name': 'Species'},
            'description': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'description_en': ('django.db.models.fields.TextField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'description_fr': ('django.db.models.fields.TextField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'description_it': ('django.db.models.fields.TextField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name_it': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'default': "'no-img.jpg'", 'max_length': '100'})
        },
        u'backend.stage': {
            'Meta': {'object_name': 'Stage'},
            'day_end': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'day_start': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'month_end': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'month_start': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name_fr': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name_it': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'picture_after': ('django.db.models.fields.files.ImageField', [], {'default': "'no-img.jpg'", 'max_length': '100'}),
            'picture_before': ('django.db.models.fields.files.ImageField', [], {'default': "'no-img.jpg'", 'max_length': '100'}),
            'picture_current': ('django.db.models.fields.files.ImageField', [], {'default': "'no-img.jpg'", 'max_length': '100'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backend.Species']"})
        },
        u'backend.survey': {
            'Meta': {'object_name': 'Survey'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'firstname_obs': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'individual': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backend.Individual']"}),
            'name_obs': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backend.Observer']", 'null': 'True', 'blank': 'True'}),
            'remark': ('django.db.models.fields.TextField', [], {'max_length': '100', 'blank': 'True'}),
            'stage': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['backend.Stage']"})
        },
        u'backend.temperature': {
            'Meta': {'object_name': 'Temperature'},
            'area': ('select2.fields.ForeignKey', [], {'to': u"orm['backend.Area']", 'search_field': "'name'"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'observer': ('select2.fields.ForeignKey', [], {'to': u"orm['backend.Observer']", 'search_field': "''"}),
            'remark': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'temperature': ('django.db.models.fields.FloatField', [], {})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['backend']