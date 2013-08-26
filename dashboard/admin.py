from django.contrib import admin
from models import Recommendation, Activity, LogEvent, GroupAssignment


admin.site.register(Recommendation)
admin.site.register(Activity)
admin.site.register(LogEvent)
admin.site.register(GroupAssignment)
