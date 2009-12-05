from webapp.librelist.models import *
from django.contrib import admin


for m in [Confirmation, UserState, MailingList, Subscription]:
    admin.site.register(m)

