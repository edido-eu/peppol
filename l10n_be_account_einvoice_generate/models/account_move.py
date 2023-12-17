# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def get_payment_identifier(self):
        """This method is designed to be inherited in localization modules"""
        ref = super(AccountMove, self).get_payment_identifier()
        if not ref:
            ref = self.payment_reference
        if self.reference_type == "bba":
            return ref.replace("+", "").replace("/", "")
        return ref
