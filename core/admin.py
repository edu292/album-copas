from django.contrib import admin

from .models import Sticker, Team


class StickerInline(admin.TabularInline):
    model = Sticker
    fields = ('slot', 'name', 'position', 'image')
    extra = 1
    ordering = ('slot',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('host_country', 'year', 'sticker_count')
    search_fields = ('host_country', 'year')
    inlines = (StickerInline,)

    @admin.display(description='Stickers')
    def sticker_count(self, obj):
        return obj.stickers.count()


@admin.register(Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'slot', 'position')
    list_filter = ('team', 'position')
    search_fields = ('name',)
