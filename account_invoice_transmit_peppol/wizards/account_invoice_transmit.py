# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models

from odoo.addons.queue_job.job import identity_exact


class AccountInvoiceSent(models.TransientModel):
    _inherit = "account.invoice.transmit"

    transmit_peppol_invoice_ids = fields.Many2many(
        "account.move",
        compute="_compute_transmit_peppol_invoice_ids",
    )
    count_transmit_peppol = fields.Integer(
        "Total by peppol",
        compute="_compute_count_transmit_peppol",
    )

    @api.depends("transmit_invoice_ids")
    def _compute_transmit_peppol_invoice_ids(self):
        self.transmit_peppol_invoice_ids = self.transmit_invoice_ids.filtered(
            lambda r: r.transmit_method_code == "peppol"
        )

    @api.depends("transmit_peppol_invoice_ids")
    def _compute_count_transmit_peppol(self):
        self.count_transmit_peppol = len(self.transmit_peppol_invoice_ids)

    def button_peppol(self):
        invoices = self.transmit_peppol_invoice_ids
        if self.resend:
            invoices.filtered("is_move_sent").is_move_sent = False
            invoices.filtered("invoice_exported").write(
                {
                    "invoice_exported": False,
                    "invoice_export_confirmed": False,
                }
            )
        description = _("Mass generating invoice for peppol sending")
        invoices.with_delay(
            description=description,
            identity_key=identity_exact,
            priority=40,
            channel="root.invoice_transmit.peppol",
        )._batch_transmit_invoice_by_peppol()
        self.env.user.notify_info(
            _("Invoices will be sent by peppol in the background.")
        )
        return {"type": "ir.actions.act_window_close"}
