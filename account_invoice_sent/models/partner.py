# -*- coding: utf-8 -*-
# Copyright 2015-2018 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    invoice_sending_method = fields.Selection(
        [("email", "Email"), ("letter", "Letter")], default=False, copy=False
    )
    invoice_amount_copy = fields.Integer(
        "Amount of invoice copies to generate",
        help="If amount = 1, then 2 invoices will be generated in the pdf "
        "(original + copy)",
    )
