from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('masters', '0003_credit_note_vfp_fields')]
    operations = [
        migrations.AddField(model_name='customer', name='mobile', field=models.CharField(blank=True, default='', max_length=15)),
        migrations.AddField(model_name='vendor', name='mobile', field=models.CharField(blank=True, default='', max_length=15)),
    ]
