from django.db import migrations, models
import django.db.models.deletion


def convertir_categories(apps, schema_editor):
    Annonce = apps.get_model("reservations", "Annonce")
    Categorie = apps.get_model("reservations", "Categorie")
    cache = {}
    for annonce in Annonce.objects.all().iterator():
        nom = getattr(annonce, "categorie_nom", "").strip()
        if not nom:
            continue
        categorie = cache.get(nom)
        if categorie is None:
            categorie = Categorie.objects.create(nom=nom)
            cache[nom] = categorie
        annonce.categorie = categorie
        annonce.save(update_fields=["categorie"])


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(model_name="annonce", old_name="categorie", new_name="categorie_nom"),
        migrations.AlterField(
            model_name="annonce",
            name="categorie_nom",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.CreateModel(
            name="Categorie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=60, unique=True)),
            ],
            options={"ordering": ["nom"]},
        ),
        migrations.AddField(
            model_name="annonce",
            name="categorie",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="annonces", to="reservations.categorie"),
        ),
        migrations.AddField(
            model_name="annonce",
            name="date_modification",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="annonces/")),
                ("ordre", models.PositiveIntegerField(default=0)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("annonce", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="reservations.annonce")),
            ],
            options={"ordering": ["ordre", "id"]},
        ),
        migrations.RunPython(convertir_categories, migrations.RunPython.noop),
        migrations.RemoveField(model_name="annonce", name="categorie_nom"),
    ]
