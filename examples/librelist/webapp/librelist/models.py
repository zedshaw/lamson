from django.db import models
from datetime import datetime
from email.utils import formataddr

# Create your models here.

class Confirmation(models.Model):
    from_address = models.EmailField()
    request_date = models.DateTimeField(auto_now_add=True)
    expected_secret = models.CharField(max_length=50)
    pending_message_id = models.CharField(max_length=200)
    list_name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.from_address

class UserState(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    state_key = models.CharField(max_length=512)
    from_address = models.EmailField()
    state = models.CharField(max_length=200)

    def __unicode__(self):
        return "%s:%s (%s)" % (self.state_key, self.from_address, self.state)

class MailingList(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    archive_url = models.CharField(max_length=512)
    archive_queue = models.CharField(max_length=512)
    name = models.CharField(max_length=512)
    similarity_pri = models.CharField(max_length=50)
    similarity_sec = models.CharField(max_length=50, null=True)

    def __unicode__(self):
        return self.name


class Subscription(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    subscriber_address = models.EmailField()
    subscriber_name = models.CharField(max_length=200)
    mailing_list = models.ForeignKey(MailingList)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return '"%s" <%s>' % (self.subscriber_name, self.subscriber_address)

    def subscriber_full_address(self):
        return formataddr((self.subscriber_name, self.subscriber_address))
