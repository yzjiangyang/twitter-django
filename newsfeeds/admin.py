from django.contrib import admin
from newsfeeds.models import NewsFeed


@admin.register(NewsFeed)
class NewsfeedAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('user', 'tweet', 'created_at')