from django.db import migrations

SUBJECTS = [
    ("Mathematics", "math", "➗", "#6366f1"),
    ("Programming", "programming", "💻", "#22c55e"),
    ("Physics", "physics", "⚛️", "#0ea5e9"),
    ("Chemistry", "chemistry", "🧪", "#f97316"),
    ("Biology", "biology", "🧬", "#10b981"),
    ("History", "history", "🏛️", "#a855f7"),
    ("Geography", "geography", "🌍", "#14b8a6"),
    ("English Language", "english", "📖", "#eab308"),
    ("Computer Science", "computer-science", "🖥️", "#3b82f6"),
    ("Economics", "economics", "📈", "#84cc16"),
    ("Astronomy", "astronomy", "🔭", "#8b5cf6"),
    ("Psychology", "psychology", "🧠", "#ec4899"),
    ("Art & Design", "art-design", "🎨", "#f43f5e"),
    ("Philosophy", "philosophy", "🦉", "#64748b"),
]


def seed_subjects(apps, schema_editor):
    Subject = apps.get_model("core", "Subject")
    for order, (name, slug, icon, color) in enumerate(SUBJECTS):
        Subject.objects.update_or_create(
            slug=slug, defaults={"name": name, "icon": icon, "color": color, "order": order}
        )


def unseed_subjects(apps, schema_editor):
    Subject = apps.get_model("core", "Subject")
    Subject.objects.filter(slug__in=[s[1] for s in SUBJECTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_subjects, unseed_subjects),
    ]
