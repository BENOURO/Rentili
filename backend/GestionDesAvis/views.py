import json

from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .forms import AvisForm
from .models import Avis


def serialize_avis(avis):
    return {
        "idAvis": avis.pk,
        "utilisateur_id": avis.utilisateur_id,
        "annonce_id": avis.annonce_id,
        "reservation_id": avis.reservation_id,
        "note": avis.note,
        "commentaire": avis.commentaire,
        "dateAvis": avis.dateAvis.isoformat(),
        "auteurRole": avis.auteurRole,
        "statut": avis.statut,
        "sentiment": avis.sentiment,
        "scoreFraude": avis.scoreFraude,
    }


@csrf_exempt
def avis_collection(request):
    if request.method == "GET":
        return lister_avis(request)

    if request.method == "POST":
        return creer_avis(request)

    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
def avis_detail(request, pk):
    if request.method == "GET":
        return consulter_avis(request, pk)

    if request.method in ("PUT", "PATCH"):
        return modifier_avis(request, pk)

    if request.method == "DELETE":
        return supprimer_avis(request, pk)

    return HttpResponseNotAllowed(["GET", "PUT", "PATCH", "DELETE"])


def lister_avis(request):
    avis_list = [serialize_avis(avis) for avis in Avis.objects.all()]
    return JsonResponse(avis_list, safe=False)


def creer_avis(request):
    data = parse_json(request)
    if isinstance(data, JsonResponse):
        return data

    form = AvisForm(data)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

    avis = form.save()
    return JsonResponse(serialize_avis(avis), status=201)


def consulter_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    return JsonResponse(serialize_avis(avis))


def modifier_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    data = parse_json(request)
    if isinstance(data, JsonResponse):
        return data

    if request.method == "PATCH":
        data = {
            "utilisateur_id": data.get("utilisateur_id", avis.utilisateur_id),
            "annonce_id": data.get("annonce_id", avis.annonce_id),
            "reservation_id": data.get("reservation_id", avis.reservation_id),
            "note": data.get("note", avis.note),
            "commentaire": data.get("commentaire", avis.commentaire),
        }

    form = AvisForm(data, instance=avis)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

    avis = form.save()
    return JsonResponse(serialize_avis(avis))


def supprimer_avis(request, pk):
    avis = get_object_or_404(Avis, pk=pk)
    avis.delete()
    return JsonResponse({}, status=204)


def parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"json": ["JSON invalide"]}}, status=400)
