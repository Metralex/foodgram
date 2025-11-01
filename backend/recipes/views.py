from django.http import HttpResponsePermanentRedirect

from recipes.models import Recipe


def recipe_shared_link(request, slug):
    try:
        recipe = Recipe.objects.get(short_url_code=slug)
    except Recipe.DoesNotExist:
        redirect_url = request.build_absolute_uri('/not_found')
    else:
        redirect_url = request.build_absolute_uri(
            f'/recipes/{recipe.id}/'
        )
    return HttpResponsePermanentRedirect(redirect_url)
