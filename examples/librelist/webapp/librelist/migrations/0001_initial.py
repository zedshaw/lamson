
from south.db import db
from django.db import models
from webapp.librelist.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Subscription'
        db.create_table('librelist_subscription', (
            ('subscriber_name', models.CharField(max_length=200)),
            ('enabled', models.BooleanField(default=True)),
            ('created_on', models.DateTimeField(auto_now_add=True)),
            ('subscriber_address', models.EmailField()),
            ('id', models.AutoField(primary_key=True)),
            ('mailing_list', models.ForeignKey(orm.MailingList)),
        ))
        db.send_create_signal('librelist', ['Subscription'])
        
        # Adding model 'UserState'
        db.create_table('librelist_userstate', (
            ('created_on', models.DateTimeField(auto_now_add=True)),
            ('state', models.CharField(max_length=200)),
            ('id', models.AutoField(primary_key=True)),
            ('state_key', models.CharField(max_length=512)),
            ('from_address', models.EmailField()),
        ))
        db.send_create_signal('librelist', ['UserState'])
        
        # Adding model 'Confirmation'
        db.create_table('librelist_confirmation', (
            ('from_address', models.EmailField()),
            ('request_date', models.DateTimeField(auto_now_add=True)),
            ('expected_secret', models.CharField(max_length=50)),
            ('pending_message_id', models.CharField(max_length=200)),
            ('list_name', models.CharField(max_length=200)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('librelist', ['Confirmation'])
        
        # Adding model 'MailingList'
        db.create_table('librelist_mailinglist', (
            ('name', models.CharField(max_length=512)),
            ('archive_url', models.CharField(max_length=512)),
            ('similarity_pri', models.CharField(max_length=50)),
            ('archive_queue', models.CharField(max_length=512)),
            ('similarity_sec', models.CharField(max_length=50, null=True)),
            ('created_on', models.DateTimeField(auto_now_add=True)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('librelist', ['MailingList'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Subscription'
        db.delete_table('librelist_subscription')
        
        # Deleting model 'UserState'
        db.delete_table('librelist_userstate')
        
        # Deleting model 'Confirmation'
        db.delete_table('librelist_confirmation')
        
        # Deleting model 'MailingList'
        db.delete_table('librelist_mailinglist')
        
    
    
    models = {
        'librelist.subscription': {
            'created_on': ('models.DateTimeField', [], {'auto_now_add': 'True'}),
            'enabled': ('models.BooleanField', [], {'default': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('models.ForeignKey', ['MailingList'], {}),
            'subscriber_address': ('models.EmailField', [], {}),
            'subscriber_name': ('models.CharField', [], {'max_length': '200'})
        },
        'librelist.userstate': {
            'created_on': ('models.DateTimeField', [], {'auto_now_add': 'True'}),
            'from_address': ('models.EmailField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'state': ('models.CharField', [], {'max_length': '200'}),
            'state_key': ('models.CharField', [], {'max_length': '512'})
        },
        'librelist.confirmation': {
            'expected_secret': ('models.CharField', [], {'max_length': '50'}),
            'from_address': ('models.EmailField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'list_name': ('models.CharField', [], {'max_length': '200'}),
            'pending_message_id': ('models.CharField', [], {'max_length': '200'}),
            'request_date': ('models.DateTimeField', [], {'auto_now_add': 'True'})
        },
        'librelist.mailinglist': {
            'archive_queue': ('models.CharField', [], {'max_length': '512'}),
            'archive_url': ('models.CharField', [], {'max_length': '512'}),
            'created_on': ('models.DateTimeField', [], {'auto_now_add': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '512'}),
            'similarity_pri': ('models.CharField', [], {'max_length': '50'}),
            'similarity_sec': ('models.CharField', [], {'max_length': '50', 'null': 'True'})
        }
    }
    
    complete_apps = ['librelist']
