from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recruitmentapp', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                IF NOT EXISTS (SELECT * FROM syscolumns WHERE id=OBJECT_ID('Applications') AND name='cover_letter')
                    ALTER TABLE Applications ADD cover_letter NVARCHAR(MAX) NULL;
                IF NOT EXISTS (SELECT * FROM syscolumns WHERE id=OBJECT_ID('Applications') AND name='motivation')
                    ALTER TABLE Applications ADD motivation NVARCHAR(MAX) NULL;
                IF NOT EXISTS (SELECT * FROM syscolumns WHERE id=OBJECT_ID('Applications') AND name='expected_salary')
                    ALTER TABLE Applications ADD expected_salary DECIMAL(10,2) NULL;
                IF NOT EXISTS (SELECT * FROM syscolumns WHERE id=OBJECT_ID('Applications') AND name='available_start_date')
                    ALTER TABLE Applications ADD available_start_date DATE NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
