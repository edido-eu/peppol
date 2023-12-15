# Copyright 2023 BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Invoice Export UBL",
    "version": "16.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Send UBL Invoice to Peppol",
    "author": "BCIM",
    "depends": [
        "account",
        "account_invoice_ubl",
        "account_invoice_transmit_method",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_invoice.xml",
        "views/peppol_server.xml",
        "views/res_config_settings.xml",
        "data/template.xml",
        "data/transmit_method.xml",
        "data/cron.xml",
    ],
    "installable": True,
}
