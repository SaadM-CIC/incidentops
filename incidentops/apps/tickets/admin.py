from django.contrib import admin
from .models import Category, Ticket, TicketHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ('field_changed', 'old_value', 'new_value', 'changed_by', 'timestamp')
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'category', 'priority', 'status', 'created_by', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description')
    inlines = [TicketHistoryInline]
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')