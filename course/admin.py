from django.contrib import admin
from .models import *

class CourseAdmin(admin.ModelAdmin):
    exclude = ('last_updated',)

class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "url")

admin.site.register(Course, CourseAdmin)
admin.site.register(Assessment, AssessmentAdmin)
