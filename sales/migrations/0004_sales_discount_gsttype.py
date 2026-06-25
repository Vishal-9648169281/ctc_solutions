from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('sales', '0003_salesinvoiceitem_description_and_more')]
    operations = [
        migrations.AddField(model_name='salesinvoiceitem', name='discount_pct', field=models.DecimalField(decimal_places=2, default=0, max_digits=5)),
        migrations.AddField(model_name='salesinvoiceitem', name='discount_amt', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='salesinvoice', name='bill_discount_pct', field=models.DecimalField(decimal_places=2, default=0, max_digits=5)),
        migrations.AddField(model_name='salesinvoice', name='gst_type', field=models.CharField(choices=[('W', 'Within State'), ('I', 'Inter State')], default='W', max_length=1)),
    ]
