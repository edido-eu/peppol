# Copyright 2023 BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Invoice Export UBL",
    "version": "10.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Send UBL Invoice to Peppol",
    "author": "BCIM",
    "depends": ["account", "account_invoice_ubl"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_invoice.xml",
        "views/peppol_server.xml",
        "views/account_config_settings.xml",
        "data/template.xml",
    ],
    "installable": True,
}
