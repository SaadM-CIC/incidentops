import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from apps.tickets.models import Category
from .classifier import classifier


@login_required
@require_POST
def suggest_view(request):
    """
    Reçoit title + description en POST,
    retourne les suggestions IA en JSON.
    """
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Données invalides'}, status=400)

    if not title and not description:
        return JsonResponse({'category_id': None, 'priority': None})

    categories = list(Category.objects.all())
    result = classifier.classify(title, description, categories)

    suggested_category = result['category']
    suggested_priority = result['priority']

    # Mapping priorité vers label français
    priority_labels = {
        'low': 'Faible',
        'medium': 'Moyenne',
        'high': 'Élevée',
        'critical': 'Critique',
    }

    return JsonResponse({
        'category_id': suggested_category.pk if suggested_category else None,
        'category_name': suggested_category.name if suggested_category else None,
        'priority': suggested_priority,
        'priority_label': priority_labels.get(suggested_priority, ''),
    })