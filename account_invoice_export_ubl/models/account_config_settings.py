# -*- coding: utf-8 -*-
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = "account.config.settings"

    peppol_server_id = fields.Many2one(related="company_id.peppol_server_id")
