# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Notification.created'
        db.add_column('mrs_notification', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2015, 8, 19, 0, 0), auto_now_add=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Notification.created'
        db.delete_column('mrs_notification', 'created')


    models = {
        'mrs.binaryresource': {
            'Meta': {'unique_together': "(('procedure', 'element_id', 'guid'),)", 'object_name': 'BinaryResource'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'conversion_complete': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'convert_before_upload': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'element_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'procedure': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.SavedProcedure']"}),
            'total_size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'upload_progress': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'uploaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'mrs.client': {
            'Meta': {'object_name': 'Client'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'mrs.clienteventlog': {
            'Meta': {'unique_together': "(('event_type', 'event_time'),)", 'object_name': 'ClientEventLog'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.Client']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'encounter_reference': ('django.db.models.fields.TextField', [], {}),
            'event_time': ('django.db.models.fields.DateTimeField', [], {}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'event_value': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'patient_reference': ('django.db.models.fields.TextField', [], {}),
            'user_reference': ('django.db.models.fields.TextField', [], {})
        },
        'mrs.notification': {
            'Meta': {'object_name': 'Notification'},
            'client': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'auto_now_add': 'True', 'blank': 'True'}),
            'delivered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'patient_id': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'procedure_id': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'mrs.patient': {
            'Meta': {'object_name': 'Patient'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'remote_identifier': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'mrs.procedure': {
            'Meta': {'object_name': 'Procedure'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'procedure': ('django.db.models.fields.TextField', [], {}),
            'procedure_guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'xml': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'mrs.queueelement': {
            'Meta': {'object_name': 'QueueElement'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'procedure': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.Procedure']"}),
            'saved_procedure': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.SavedProcedure']"})
        },
        'mrs.requestlog': {
            'Meta': {'object_name': 'RequestLog'},
            'duration': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '767'})
        },
        'mrs.savedprocedure': {
            'Meta': {'object_name': 'SavedProcedure'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.Client']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'encounter': ('django.db.models.fields.CharField', [], {'default': "'-1'", 'max_length': '512'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'procedure_guid': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'responses': ('django.db.models.fields.TextField', [], {}),
            'upload_password': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'upload_username': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'uploaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['mrs']