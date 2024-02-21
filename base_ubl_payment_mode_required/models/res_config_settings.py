# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    ubl_payment_mode_required = fields.Boolean(
        related="company_id.ubl_payment_mode_required",
        readonly=False,
    )
