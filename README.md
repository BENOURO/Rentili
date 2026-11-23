# RENTILI — Rent Everything, Everywhere, Anytime

Plateforme de location d'objets entre particuliers. Projet de génie logiciel (Scrum).

- `backend/` — API REST **Django + Django REST Framework**, authentification **JWT**
- `frontend/` — interface **React (Vite) + React Router**

## Lancer le projet

**Backend** (terminal 1) :
```bash
cd backend
python -m venv venv
# Windows : venv\Scripts\activate      macOS / Linux : source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # comptes de démonstration (mot de passe : rentili2026)
python manage.py seed_reservations  # objets et réservations de démonstration (après seed_demo)
python manage.py runserver          # http://127.0.0.1:8000 (port attendu par frontend/vite.config.js)
```

**Frontend** (terminal 2) :
```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```
En développement, Vite transmet les appels `/api/...` au backend (voir `frontend/vite.config.js`).

Comptes de démo : `yasmine@rentili.tn`, `karim@rentili.tn` (membres), `admin@rentili.tn` (admin → http://127.0.0.1:8000/admin).
Tests du backend : `cd backend && pytest`.

## Organisation

| Module | Backend (app Django) | Frontend | Responsable |
|---|---|---|---|
| Gestion des utilisateurs | `backend/users/` | `frontend/src/pages/users/` | Ghassen Barhoumi |
| Gestion des annonces | `backend/reservations/` (modèles `Annonce`, `Categorie`, `Photo`) | `frontend/src/pages/reservations/` (`Annonces*`, `AnnonceFormPage`) | Youssef Marzouki |
| Gestion des réservations | `backend/reservations/` | `frontend/src/pages/reservations/` | Ghassen Barhoumi |
| Avis & administration | `backend/GestionDesAvis/` | `frontend/src/pages/AvisPage.jsx`, `frontend/src/components/reviews/` | Amine Bennour |
| Messagerie & communication | `backend/messaging/` | `frontend/src/pages/messaging/` | Eya Raddaoui |

Règles communes :
- une branche par fonctionnalité (`feature/...`), fusion dans `main` par pull request relue ;
- l'utilisateur est **`users.User`** (connexion par email) : dans les modèles, `models.ForeignKey(settings.AUTH_USER_MODEL, ...)`,
  jamais `from django.contrib.auth.models import User` ;
- routes API sous `/api/<module>/` ; toutes les routes exigent un utilisateur connecté sauf mention `AllowAny` ;
- côté React, appeler l'API avec `api()` de `src/api/client.js` (le jeton est ajouté et renouvelé automatiquement),
  et l'utilisateur connecté avec `useAuth()` de `src/auth/AuthContext.jsx` ;
- une page réservée aux membres s'entoure de `<ProtectedRoute>` dans `src/App.jsx`.

## API du module « Gestion des utilisateurs » (Sprint 1)

| Méthode | Route | Rôle | US |
|---|---|---|---|
| POST | `/api/auth/register/` | inscription (Create) → `{access, refresh, user}` | US01 |
| POST | `/api/auth/login/` | connexion `{email, password}` → `{access, refresh, user}` | US02 |
| POST | `/api/auth/refresh/` | renouveler le jeton d'accès `{refresh}` | US02 |
| GET | `/api/users/me/` | mon profil (Read) | US03 |
| PATCH | `/api/users/me/` | modifier mon profil (Update ; JSON, ou multipart pour la photo) | US04 |
| DELETE | `/api/users/me/` | supprimer mon compte (Delete : anonymisation, signal `user_deleted`) | US06 |
| GET | `/api/users/` | liste des membres (public) | US05 |
| GET | `/api/users/<id>/` | profil public : sans email ni téléphone | US05 |

La déconnexion (US02) se fait côté client : le front supprime ses jetons.
Mots de passe hachés et validés par Django ; jetons JWT (accès 30 min, rafraîchissement 7 jours) ;
suppression de compte par anonymisation, pour que l'historique des réservations et des avis reste cohérent.

Les autres modules peuvent réagir à une suppression de compte :
```python
from django.dispatch import receiver
from users.signals import user_deleted

@receiver(user_deleted)
def archiver_annonces(sender, user, **kwargs):
    Listing.objects.filter(owner=user).update(status="archived")
```

Prévu au sprint « authentification intelligente » : vérification de l'adresse email, réinitialisation et changement
du mot de passe, gestion des rôles, connexion Google (OAuth), révocation des jetons à la déconnexion,
limitation des tentatives de connexion.

## API du module « Gestion des réservations » (Sprint 1)

Les réservations portent sur les annonces du module « Gestion des annonces » (modèles `Annonce`,
`Categorie` et `Photo`, dans la même app `reservations`) : `Reservation.annonce` est une clé étrangère
vers `Annonce`, et le propriétaire d'une réservation est `annonce.proprietaire`.

| Méthode | Route | Rôle | US |
|---|---|---|---|
| POST | `/api/reservations/` | demander une réservation `{annonce_id, date_debut, date_fin, message}` : prix calculé, chevauchements refusés | US21 |
| POST | `/api/reservations/<id>/accepter/` | le propriétaire accepte (les demandes concurrentes sont refusées) | US22 |
| POST | `/api/reservations/<id>/refuser/` | le propriétaire refuse `{motif}` | US22 |
| GET | `/api/reservations/?role=locataire\|proprietaire&statut=…` | mes réservations envoyées / reçues | US23 |
| GET | `/api/reservations/<id>/` | détail (locataire ou propriétaire seulement) | US23 |
| POST | `/api/reservations/<id>/annuler/` | annuler une demande en attente ou une réservation pas encore commencée | US24 |
| PATCH | `/api/reservations/<id>/` | le locataire modifie les dates d'une demande en attente (prix recalculé) | US25 |
| POST | `/api/reservations/<id>/terminer/` | le propriétaire clôt une location commencée | US26 |

Statuts : `EN_ATTENTE` → `ACCEPTEE` → `TERMINEE`, ou `REFUSEE` / `ANNULEE`.
Quand un compte est supprimé (signal `user_deleted`), ses demandes en attente et ses réservations à venir sont annulées.

## API du module « Gestion des annonces » (Sprint 1)

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/reservations/annonces/` | liste publique des annonces actives ; filtres `search`, `categorie`, `ville`, `prix_min`, `prix_max`, `date_debut` + `date_fin` (objets libres sur la période), `mine=true` (mes annonces) |
| POST | `/api/reservations/annonces/` | publier une annonce (connecté), photos en multipart |
| GET | `/api/reservations/annonces/<id>/` | détail public, avec les périodes déjà réservées |
| PATCH | `/api/reservations/annonces/<id>/` | modifier son annonce (propriétaire seulement) |
| DELETE | `/api/reservations/annonces/<id>/` | retirer son annonce (désactivée, pas effacée) : ses demandes en attente et réservations à venir sont annulées |
| GET | `/api/reservations/annonces/categories/` | liste des catégories |
