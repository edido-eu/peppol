# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def get_payment_identifier(self):
        """This method is designed to be inherited in localization modules"""
        super(AccountInvoice, self).get_payment_identifier()
        if self.reference_type == "bba":
            return self.reference.replace("+", "").replace("/", "")
        else:
            return self.reference
        return None
