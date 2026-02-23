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
        # Tag.name — unique constraint already in DB
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='tag',
                    name='name',
                    field=models.CharField(max_length=50, unique=True),
                ),
            ],
            database_operations=[],
        ),
        # short_url — db_index already covered by unique index
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='url',
                    name='short_url',
                    field=models.CharField(db_index=True, max_length=10, unique=True),
                ),
            ],
            database_operations=[],
        ),
        # created_at — db_index already in DB
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='url',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True, db_index=True),
                ),
            ],
            database_operations=[],
        ),
        # custom_alias — column already in DB
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='url',
                    name='custom_alias',
                    field=models.CharField(blank=True, max_length=50, null=True, unique=True),
                ),
            ],
            database_operations=[],
        ),
        # title — column already in DB
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='url',
                    name='title',
                    field=models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
            database_operations=[],
        ),
        # description — column already in DB
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='url',
                    name='description',
                    field=models.CharField(blank=True, max_length=500, null=True),
                ),
            ],
            database_operations=[],
        ),
        # favicon — column already in DB
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='url',
                    name='favicon',
                    field=models.CharField(blank=True, max_length=2000, null=True),
                ),
            ],
            database_operations=[],
        ),
    ]
