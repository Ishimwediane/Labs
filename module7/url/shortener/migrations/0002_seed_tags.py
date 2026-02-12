from django.db import migrations

def create_default_tags(apps, schema_editor):
    Tag = apps.get_model('shortener', 'Tag')
    default_tags = ["Marketing", "Social Media", "Newsletter", "Personal"]
    
    for tag_name in default_tags:
        Tag.objects.get_or_create(name=tag_name)

class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_tags),
    ]
