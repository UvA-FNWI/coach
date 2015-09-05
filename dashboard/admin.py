from django.contrib import admin
from .models import *

class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user','verb', 'activity', 'type', 'course')

admin.site.register(Activity, ActivityAdmin)
admin.site.register(GroupAssignment)
