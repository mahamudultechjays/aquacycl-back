from django.contrib import admin

from . import models

# Register your models here.

admin.site.register(models.UserProfileDetails)
admin.site.register(models.UserSiteMapping)
