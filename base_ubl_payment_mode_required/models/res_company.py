# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    ubl_payment_mode_required = fields.Boolean(
        string="Payment mode required for UBL documents",
        help="Check this if payment mode should be required in UBL documents",
    )
