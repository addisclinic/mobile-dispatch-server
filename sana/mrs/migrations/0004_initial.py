# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Client'
        db.create_table('mrs_client', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('last_seen', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('mrs', ['Client'])

        # Adding model 'ClientEventLog'
        db.create_table('mrs_clienteventlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.Client'])),
            ('event_type', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('event_value', self.gf('django.db.models.fields.TextField')()),
            ('event_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('encounter_reference', self.gf('django.db.models.fields.TextField')()),
            ('patient_reference', self.gf('django.db.models.fields.TextField')()),
            ('user_reference', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('mrs', ['ClientEventLog'])

        # Adding unique constraint on 'ClientEventLog', fields ['event_type', 'event_time']
        db.create_unique('mrs_clienteventlog', ['event_type', 'event_time'])

        # Adding model 'Patient'
        db.create_table('mrs_patient', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('remote_identifier', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('mrs', ['Patient'])

        # Adding model 'Procedure'
        db.create_table('mrs_procedure', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('procedure_guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('procedure', self.gf('django.db.models.fields.TextField')()),
            ('xml', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('mrs', ['Procedure'])

        # Adding model 'BinaryResource'
        db.create_table('mrs_binaryresource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('procedure', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.SavedProcedure'])),
            ('element_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('data', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('upload_progress', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('total_size', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('uploaded', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('convert_before_upload', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('conversion_complete', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('mrs', ['BinaryResource'])

        # Adding unique constraint on 'BinaryResource', fields ['procedure', 'element_id', 'guid']
        db.create_unique('mrs_binaryresource', ['procedure_id', 'element_id', 'guid'])

        # Adding model 'SavedProcedure'
        db.create_table('mrs_savedprocedure', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('procedure_guid', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.Client'])),
            ('responses', self.gf('django.db.models.fields.TextField')()),
            ('upload_username', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('upload_password', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('uploaded', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('encounter', self.gf('django.db.models.fields.CharField')(default='-1', max_length=512)),
        ))
        db.send_create_signal('mrs', ['SavedProcedure'])

        # Adding model 'Notification'
        db.create_table('mrs_notification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.Client'])),
            ('patient_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.Patient'])),
            ('procedure_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.Procedure'])),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('delivered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('mrs', ['Notification'])

        # Adding model 'QueueElement'
        db.create_table('mrs_queueelement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('procedure', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.Procedure'])),
            ('saved_procedure', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mrs.SavedProcedure'])),
            ('finished', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('mrs', ['QueueElement'])

        # Adding model 'RequestLog'
        db.create_table('mrs_requestlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uri', self.gf('django.db.models.fields.CharField')(max_length=767)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('duration', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('mrs', ['RequestLog'])


    def backwards(self, orm):
        # Removing unique constraint on 'BinaryResource', fields ['procedure', 'element_id', 'guid']
        db.delete_unique('mrs_binaryresource', ['procedure_id', 'element_id', 'guid'])

        # Removing unique constraint on 'ClientEventLog', fields ['event_type', 'event_time']
        db.delete_unique('mrs_clienteventlog', ['event_type', 'event_time'])

        # Deleting model 'Client'
        db.delete_table('mrs_client')

        # Deleting model 'ClientEventLog'
        db.delete_table('mrs_clienteventlog')

        # Deleting model 'Patient'
        db.delete_table('mrs_patient')

        # Deleting model 'Procedure'
        db.delete_table('mrs_procedure')

        # Deleting model 'BinaryResource'
        db.delete_table('mrs_binaryresource')

        # Deleting model 'SavedProcedure'
        db.delete_table('mrs_savedprocedure')

        # Deleting model 'Notification'
        db.delete_table('mrs_notification')

        # Deleting model 'QueueElement'
        db.delete_table('mrs_queueelement')

        # Deleting model 'RequestLog'
        db.delete_table('mrs_requestlog')


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
            'Meta': {'ordering': "['-created']", 'object_name': 'Notification'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.Client']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'patient_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.Patient']"}),
            'procedure_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mrs.Procedure']"})
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