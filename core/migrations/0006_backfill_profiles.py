from django.db import migrations


def backfill_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("core", "Profile")
    for user in User.objects.filter(profile__isnull=True):
        role = "admin" if user.is_superuser else "student"
        Profile.objects.create(user=user, role=role)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_testsession_difficulty_testsession_source_profile_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_profiles, noop_reverse),
    ]
