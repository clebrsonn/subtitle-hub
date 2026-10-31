from django.contrib import admin
from .models import Work, Episode, ExternalMapping, SubtitleBlob, SubtitleEntry, AniDBState

class SubtitleEntryAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'language', 'status', 'work', 'episode')
    list_filter = ('status', 'language', 'is_forced')
    search_fields = ('original_filename', 'release_group')

class ExternalMappingAdmin(admin.ModelAdmin):
    list_display = ('provider', 'external_id', 'work', 'episode', 'status', 'is_manual_override')
    list_filter = ('provider', 'status', 'is_manual_override')
    search_fields = ('external_id',)

admin.site.register(Work)
admin.site.register(Episode)
admin.site.register(ExternalMapping, ExternalMappingAdmin)
admin.site.register(SubtitleBlob)
admin.site.register(SubtitleEntry, SubtitleEntryAdmin)
admin.site.register(AniDBState)
