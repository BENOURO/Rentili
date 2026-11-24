"""Tests du module « Gestion des réservations » (US21 à US26)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from reservations.models import Annonce, Categorie, Reservation
from users.models import User

J = lambda n: date.today() + timedelta(days=n)  # noqa: E731
S = Reservation.Statut


def client_pour(user):
    c = APIClient()
    r = c.post("/api/auth/login/", {"email": user.email, "password": "pass-12345"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    return c


@pytest.fixture
def proprio(db):
    return User.objects.create_user("proprio@test.tn", "pass-12345", first_name="Nour", last_name="Kefi", city="Tunis")


@pytest.fixture
def locataire(db):
    return User.objects.create_user("loc@test.tn", "pass-12345", first_name="Aziz", last_name="Mansour", city="Sfax")


@pytest.fixture
def tiers(db):
    return User.objects.create_user("tiers@test.tn", "pass-12345", first_name="Rim", last_name="Zouari")


@pytest.fixture
def annonce(proprio):
    return Annonce.objects.create(proprietaire=proprio, titre="Perceuse Bosch", prix_jour=Decimal("15"), caution=Decimal("100"))


@pytest.fixture
def cl_loc(locataire):
    return client_pour(locataire)


@pytest.fixture
def cl_proprio(proprio):
    return client_pour(proprio)


def demander(client, annonce, debut, fin, **extra):
    return client.post(
        "/api/reservations/",
        {"annonce_id": annonce.pk, "date_debut": debut.isoformat(), "date_fin": fin.isoformat(), **extra},
        format="json",
    )


# --- US21 : demander une réservation -----------------------------------------------------------

def test_demande_cree_en_attente_avec_prix_calcule(cl_loc, annonce):
    r = demander(cl_loc, annonce, J(2), J(4), message="Pour un week-end")
    assert r.status_code == 201
    assert r.data["statut"] == "EN_ATTENTE"
    assert r.data["nb_jours"] == 3
    assert Decimal(r.data["prix_total"]) == Decimal("45")  # 3 jours × 15 DT
    assert Decimal(r.data["caution"]) == Decimal("100")


def test_demande_refusee_sans_connexion(annonce):
    assert demander(APIClient(), annonce, J(2), J(4)).status_code == 401


@pytest.mark.parametrize("debut,fin,champ", [(-1, 2, "date_debut"), (5, 3, "date_fin"), (1, 100, "date_fin")])
def test_dates_invalides(cl_loc, annonce, debut, fin, champ):
    r = demander(cl_loc, annonce, J(debut), J(fin))
    assert r.status_code == 400 and champ in r.data


def test_impossible_de_reserver_son_propre_objet(cl_proprio, annonce):
    r = demander(cl_proprio, annonce, J(2), J(3))
    assert r.status_code == 400 and "annonce_id" in r.data


def test_chevauchement_avec_une_reservation_acceptee(cl_loc, annonce, tiers):
    Reservation.objects.create(annonce=annonce, locataire=tiers, date_debut=J(5), date_fin=J(8),
                               statut=S.ACCEPTEE, prix_total=60, caution=100)
    assert demander(cl_loc, annonce, J(7), J(10)).status_code == 400
    assert demander(cl_loc, annonce, J(9), J(10)).status_code == 201  # juste après : libre


def test_pas_deux_demandes_en_attente_sur_les_memes_dates(cl_loc, annonce):
    assert demander(cl_loc, annonce, J(2), J(4)).status_code == 201
    assert demander(cl_loc, annonce, J(3), J(5)).status_code == 400


# --- US22 : accepter ou refuser ----------------------------------------------------------------

def test_proprietaire_accepte_et_les_demandes_concurrentes_sont_refusees(cl_loc, cl_proprio, annonce, tiers):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    autre = Reservation.objects.create(annonce=annonce, locataire=tiers, date_debut=J(3), date_fin=J(6),
                                       prix_total=60, caution=100)
    r = cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert r.status_code == 200 and r.data["statut"] == "ACCEPTEE"
    autre.refresh_from_db()
    assert autre.statut == S.REFUSEE and autre.motif_refus


def test_proprietaire_refuse_avec_motif(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    r = cl_proprio.post(f"/api/reservations/{rid}/refuser/", {"motif": "Objet en réparation"}, format="json")
    assert r.status_code == 200
    assert r.data["statut"] == "REFUSEE" and r.data["motif_refus"] == "Objet en réparation"


def test_le_locataire_ne_peut_pas_accepter_sa_propre_demande(cl_loc, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    assert cl_loc.post(f"/api/reservations/{rid}/accepter/").status_code == 403


def test_on_ne_peut_pas_accepter_deux_fois(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert cl_proprio.post(f"/api/reservations/{rid}/refuser/").status_code == 400


# --- US23 : consulter mes réservations ----------------------------------------------------------

def test_listes_locataire_et_proprietaire(cl_loc, cl_proprio, annonce, tiers):
    demander(cl_loc, annonce, J(2), J(4))
    assert len(cl_loc.get("/api/reservations/?role=locataire").data) == 1
    assert len(cl_loc.get("/api/reservations/?role=proprietaire").data) == 0
    recues = cl_proprio.get("/api/reservations/?role=proprietaire").data
    assert len(recues) == 1 and recues[0]["role"] == "proprietaire"
    assert recues[0]["actions"]["accepter"] is True
    assert "email" not in recues[0]["locataire"]


def test_un_tiers_ne_voit_pas_la_reservation(cl_loc, annonce, tiers):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    c = client_pour(tiers)
    assert c.get("/api/reservations/").data == []
    assert c.get(f"/api/reservations/{rid}/").status_code == 404


def test_filtre_par_statut(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    demander(cl_loc, annonce, J(10), J(11))
    cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert len(cl_loc.get("/api/reservations/?statut=ACCEPTEE").data) == 1


# --- US24 : annuler -----------------------------------------------------------------------------

def test_locataire_annule_une_demande_en_attente(cl_loc, annonce, locataire):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    r = cl_loc.post(f"/api/reservations/{rid}/annuler/")
    assert r.status_code == 200 and r.data["statut"] == "ANNULEE"
    assert Reservation.objects.get(pk=rid).annulee_par == locataire


def test_proprietaire_annule_une_reservation_acceptee_a_venir(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert cl_proprio.post(f"/api/reservations/{rid}/annuler/").data["statut"] == "ANNULEE"


def test_impossible_d_annuler_une_location_commencee(cl_loc, annonce, locataire):
    r = Reservation.objects.create(annonce=annonce, locataire=locataire, date_debut=date.today(), date_fin=J(2),
                                   statut=S.ACCEPTEE, prix_total=45, caution=100)
    assert cl_loc.post(f"/api/reservations/{r.pk}/annuler/").status_code == 400


# --- US25 : modifier les dates ------------------------------------------------------------------

def test_locataire_modifie_les_dates_et_le_prix_est_recalcule(cl_loc, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    r = cl_loc.patch(f"/api/reservations/{rid}/", {"date_fin": J(6).isoformat()}, format="json")
    assert r.status_code == 200
    assert r.data["nb_jours"] == 5 and Decimal(r.data["prix_total"]) == Decimal("75")


def test_modification_impossible_apres_acceptation(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert cl_loc.patch(f"/api/reservations/{rid}/", {"date_fin": J(6).isoformat()}, format="json").status_code == 400


def test_le_proprietaire_ne_modifie_pas_les_dates(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    assert cl_proprio.patch(f"/api/reservations/{rid}/", {"date_fin": J(6).isoformat()}, format="json").status_code == 403


# --- US26 : terminer la location ----------------------------------------------------------------

def test_proprietaire_termine_une_location_commencee(cl_proprio, annonce, locataire):
    r = Reservation.objects.create(annonce=annonce, locataire=locataire, date_debut=J(-3), date_fin=J(-1),
                                   statut=S.ACCEPTEE, prix_total=45, caution=100)
    res = cl_proprio.post(f"/api/reservations/{r.pk}/terminer/")
    assert res.status_code == 200 and res.data["statut"] == "TERMINEE"


def test_impossible_de_terminer_avant_le_debut(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert cl_proprio.post(f"/api/reservations/{rid}/terminer/").status_code == 400


# --- Intégration avec le module utilisateurs ------------------------------------------------------

def test_suppression_du_compte_annule_les_reservations_a_venir(cl_loc, annonce, locataire):
    rid = demander(cl_loc, annonce, J(2), J(4)).data["id"]
    assert cl_loc.delete("/api/users/me/", {"password": "pass-12345"}, format="json").status_code == 204
    assert Reservation.objects.get(pk=rid).statut == S.ANNULEE


def test_annonces_publiques_avec_periodes_reservees(annonce, locataire):
    Reservation.objects.create(annonce=annonce, locataire=locataire, date_debut=J(5), date_fin=J(8),
                               statut=S.ACCEPTEE, prix_total=60, caution=100)
    c = APIClient()
    assert c.get("/api/reservations/annonces/").data["count"] == 1
    d = c.get(f"/api/reservations/annonces/{annonce.pk}/").data
    assert d["periodes_reservees"] == [{"date_debut": J(5), "date_fin": J(8)}]


# --- US13 à US18 : gestion complète des annonces ----------------------------------------------

def test_publication_annonce_valide(cl_proprio):
    categorie = Categorie.objects.create(nom="Outils")
    r = cl_proprio.post("/api/reservations/annonces/", {
        "titre": "Pistolet à peinture",
        "description": "Fourni avec un kit complet.",
        "categorie_id": categorie.pk,
        "ville": "Tunis",
        "prix_jour": "35",
        "caution": "200",
    }, format="json")
    assert r.status_code == 201
    assert r.data["titre"] == "Pistolet à peinture"
    assert r.data["categorie"]["nom"] == "Outils"


def test_publication_refusee_sans_connexion(db):
    r = APIClient().post("/api/reservations/annonces/", {"titre": "Objet"}, format="json")
    assert r.status_code == 401


def test_publication_refusee_si_champs_invalides(cl_proprio):
    r = cl_proprio.post("/api/reservations/annonces/", {
        "titre": "", "description": "", "ville": "", "prix_jour": "-1", "caution": "-5",
    }, format="json")
    assert r.status_code == 400


def test_liste_filtres_pagination_et_disponibilite(cl_loc, annonce, locataire):
    categorie = Categorie.objects.create(nom="Bricolage")
    annonce.categorie = categorie
    annonce.ville = "Tunis"
    annonce.save()
    r = cl_loc.get("/api/reservations/annonces/?categorie=Tunis")
    assert r.status_code == 200

    r = cl_loc.get("/api/reservations/annonces/?categorie=Bricolage&ville=Tunis&prix_min=10&prix_max=20")
    assert r.status_code == 200 and r.data["count"] == 1

    Reservation.objects.create(
        annonce=annonce, locataire=locataire, date_debut=J(5), date_fin=J(8),
        statut=S.ACCEPTEE, prix_total=60, caution=100,
    )
    r = cl_loc.get(f"/api/reservations/annonces/?date_debut={J(6).isoformat()}&date_fin={J(7).isoformat()}")
    assert r.status_code == 200 and r.data["count"] == 0


def test_detail_ouvert_a_tous(cl_loc, annonce):
    r = cl_loc.get(f"/api/reservations/annonces/{annonce.pk}/")
    assert r.status_code == 200
    assert r.data["description"] == annonce.description


def test_seul_le_proprietaire_modifie_l_annonce(cl_proprio, cl_loc, annonce):
    r = cl_loc.patch(f"/api/reservations/annonces/{annonce.pk}/", {"titre": "Titre tiers"}, format="json")
    assert r.status_code == 404
    r = cl_proprio.patch(f"/api/reservations/annonces/{annonce.pk}/", {"titre": "Titre modifié"}, format="json")
    assert r.status_code == 200
    assert r.data["titre"] == "Titre modifié"


def test_suppression_archive_sans_supprimer_reservations(cl_proprio, cl_loc, annonce, locataire):
    resa = Reservation.objects.create(
        annonce=annonce, locataire=locataire, date_debut=J(5), date_fin=J(6),
        statut=S.EN_ATTENTE, prix_total=30, caution=100,
    )
    r = cl_proprio.delete(f"/api/reservations/annonces/{annonce.pk}/")
    assert r.status_code == 204
    annonce.refresh_from_db()
    assert annonce.active is False
    assert Reservation.objects.filter(pk=resa.pk).exists()
    assert APIClient().get(f"/api/reservations/annonces/{annonce.pk}/").status_code == 404


def test_retirer_une_annonce_annule_ses_reservations_a_venir(cl_loc, cl_proprio, annonce, tiers, proprio):
    en_attente = demander(cl_loc, annonce, J(5), J(7)).data["id"]
    acceptee = Reservation.objects.create(annonce=annonce, locataire=tiers, date_debut=J(10), date_fin=J(12),
                                          statut=S.ACCEPTEE, prix_total=45, caution=100)
    en_cours = Reservation.objects.create(annonce=annonce, locataire=tiers, date_debut=J(-1), date_fin=J(1),
                                          statut=S.ACCEPTEE, prix_total=45, caution=100)
    terminee = Reservation.objects.create(annonce=annonce, locataire=tiers, date_debut=J(-9), date_fin=J(-7),
                                          statut=S.TERMINEE, prix_total=45, caution=100)

    assert cl_proprio.delete(f"/api/reservations/annonces/{annonce.pk}/").status_code == 204
    statuts = {r.pk: r.statut for r in Reservation.objects.all()}
    assert statuts[en_attente] == S.ANNULEE
    assert statuts[acceptee.pk] == S.ANNULEE
    assert statuts[en_cours.pk] == S.ACCEPTEE
    assert statuts[terminee.pk] == S.TERMINEE
    assert Reservation.objects.get(pk=en_attente).annulee_par == proprio


def test_impossible_d_accepter_sur_une_annonce_retiree(cl_loc, cl_proprio, annonce):
    rid = demander(cl_loc, annonce, J(5), J(7)).data["id"]
    Annonce.objects.filter(pk=annonce.pk).update(active=False)
    r = cl_proprio.post(f"/api/reservations/{rid}/accepter/")
    assert r.status_code == 400 and "retirée" in r.data["detail"]


def test_mes_annonces_n_affiche_pas_les_annonces_retirees(cl_proprio, annonce):
    assert cl_proprio.get("/api/reservations/annonces/?mine=true").data["count"] == 1
    cl_proprio.delete(f"/api/reservations/annonces/{annonce.pk}/")
    assert cl_proprio.get("/api/reservations/annonces/?mine=true").data["count"] == 0
