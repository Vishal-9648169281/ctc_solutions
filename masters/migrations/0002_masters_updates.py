from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0001_initial'),
    ]

    operations = [
        # Product: add company field
        migrations.AddField(
            model_name='product',
            name='company',
            field=models.CharField(max_length=200, blank=True, default=''),
            preserve_default=False,
        ),

        # Party: add gst_type, amc_start_date, amc_end_date
        migrations.AddField(
            model_name='party',
            name='gst_type',
            field=models.CharField(
                max_length=1,
                choices=[('I', 'Inter State'), ('W', 'Within State')],
                default='W',
            ),
        ),
        migrations.AddField(
            model_name='party',
            name='amc_start_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='party',
            name='amc_end_date',
            field=models.DateField(null=True, blank=True),
        ),

        # GeneralLedgerMaster: rename name→description, rename code→ledger_code, add ledger_group
        migrations.RenameField(
            model_name='generalledgermaster',
            old_name='name',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='generalledgermaster',
            old_name='code',
            new_name='ledger_code',
        ),
        migrations.AlterField(
            model_name='generalledgermaster',
            name='description',
            field=models.CharField(max_length=200, default=''),
        ),
        migrations.AlterField(
            model_name='generalledgermaster',
            name='ledger_code',
            field=models.CharField(max_length=20, unique=True, default=''),
        ),
        migrations.RemoveField(
            model_name='generalledgermaster',
            name='account_type',
        ),
        migrations.AddField(
            model_name='generalledgermaster',
            name='ledger_group',
            field=models.CharField(
                max_length=30,
                default='OTHER',
                choices=[
                    ('PURCHASES', 'Purchases'),
                    ('SALES', 'Sales'),
                    ('EXPENSES_PAYABLE', 'Expenses Payable'),
                    ('BANK', 'Bank Accounts'),
                    ('CASH', 'Cash in Hand'),
                    ('SUNDRY_DEBTOR', 'Sundry Debtors'),
                    ('SUNDRY_CREDITOR', 'Sundry Creditors'),
                    ('DUTIES_TAXES', 'Duties & Taxes'),
                    ('FIXED_ASSETS', 'Fixed Assets'),
                    ('CAPITAL', 'Capital Account'),
                    ('OTHER', 'Other'),
                ],
            ),
        ),
    ]
