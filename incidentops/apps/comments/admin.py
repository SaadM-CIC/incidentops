from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal',)