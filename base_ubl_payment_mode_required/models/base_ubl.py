# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, models
from odoo.exceptions import Warning as UserError


class BaseUBL(models.AbstractModel):
    _inherit = "base.ubl"

    def _ubl_add_payment_means(
        self,
        partner_bank,
        payment_mode,
        date_due,
        parent_node,
        ns,
        payment_identifier=None,
        version="2.1",
    ):
        if not payment_mode:
            raise UserError(_("You must define a payment mode on the invoice"))
        return super(BaseUBL, self)._ubl_add_payment_means(
            partner_bank,
            payment_mode,
            date_due,
            parent_node,
            ns,
            payment_identifier=payment_identifier,
            version=version,
        )
