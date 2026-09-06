from django.db import migrations, models


def forwards_map_old_statuses(apps, schema_editor):
    """
    Map the old status values onto the new client-facing workflow so
    existing data doesn't end up in a status that no longer exists.

    old 'pending'    -> new 'submitted'  (just requested, nothing accepted yet)
    old 'collected'  -> new 'collected'  (unchanged)
    old 'processing' -> new 'pending'    (staff are handling it -> pending pickup/completion)
    old 'completed'  -> new 'completed'  (unchanged)
    """
    WasteCollection = apps.get_model('recycling', 'WasteCollection')
    WasteCollection.objects.filter(status='pending').update(status='submitted')
    WasteCollection.objects.filter(status='processing').update(status='pending')


def backwards_map_new_statuses(apps, schema_editor):
    WasteCollection = apps.get_model('recycling', 'WasteCollection')
    WasteCollection.objects.filter(status='submitted').update(status='pending')
    WasteCollection.objects.filter(status='pending').update(status='processing')


class Migration(migrations.Migration):

    dependencies = [
        ('recycling', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_map_old_statuses, backwards_map_new_statuses),
        migrations.AlterField(
            model_name='wastecollection',
            name='status',
            field=models.CharField(
                choices=[
                    ('submitted', 'Submitted for Collection'),
                    ('pending', 'Pending Pickup'),
                    ('collected', 'Collected'),
                    ('completed', 'Completed'),
                ],
                default='submitted',
                max_length=20,
            ),
        ),
    ]
