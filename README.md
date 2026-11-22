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
python manage.py seed_demo        # comptes de démonstration (mot de passe : rentili2026)
python manage.py runserver        # http://127.0.0.1:8000
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
| Gestion des annonces | `backend/listings/` | `frontend/src/pages/listings/` | Youssef Marzouki |
| Gestion des réservations | `backend/bookings/` | `frontend/src/pages/bookings/` | Ghayth Ben Othmen |
| Avis & administration | `backend/reviews/` | `frontend/src/pages/reviews/` | Amine Bennour |
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
