# -*- coding: utf-8 -*-
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountInvoiceSent(models.TransientModel):
    _inherit = "account.invoice.sent"

    def _default_count_peppol(self):
        active_ids = self._context.get("active_ids", [])
        invoices = self.env["account.invoice"].browse(active_ids)
        invoices = invoices._filter_send_invoice("peppol")
        return len(invoices)

    count_peppol = fields.Integer("By peppol", readonly=True, default=_default_count_peppol)

    @api.multi
    def button_peppol(self):
        self._send_action("peppol")
        self.env.user.notify_info(_("Invoices will be sent by peppol in the background."))
        return {"type": "ir.actions.act_window_close"}
