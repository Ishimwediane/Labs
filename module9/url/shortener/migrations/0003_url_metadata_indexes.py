from django.db import migrations, models


class Migration(migrations.Migration):
    """
    State-only migration: all schema changes already exist in the database
    from a previous (partial) migration run. This migration only updates
    Django's migration state to match the actual DB schema.
    """

    dependencies = [
        ('shortener', '0002_seed_tags'),
    ]

    operations = [
        # Tag.name — unique constraint
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
        # short_url — db_index
        migrations.AlterField(
            model_name='url',
            name='short_url',
            field=models.CharField(db_index=True, max_length=10, unique=True),
        ),
        # created_at — db_index
        migrations.AlterField(
            model_name='url',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        # custom_alias — column
        migrations.AddField(
            model_name='url',
            name='custom_alias',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        # title — column
        migrations.AddField(
            model_name='url',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        # description — column
        migrations.AddField(
            model_name='url',
            name='description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        # favicon — column
        migrations.AddField(
            model_name='url',
            name='favicon',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
    ]
