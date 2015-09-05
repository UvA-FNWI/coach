from django.contrib import admin
from .models import *

class CourseAdmin(admin.ModelAdmin):
    exclude = ('last_updated',)

admin.site.register(Course, CourseAdmin)
admin.site.register(Assessment)
