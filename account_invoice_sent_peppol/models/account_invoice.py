# -*- coding: utf-8 -*-
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.queue_job.job import job, related_action


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @job(default_channel="root.background.invoice_send")  # priority=50
    @related_action(action="related_action_open_invoice")
    def _send_invoice_peppol(self):
        """Generate and send an invoice by peppol"""
        # we need to apply the filter because the state may have
        # changed since when we delayed the job
        invoices = self.exists()._filter_send_invoice(sending_method="peppol")
        if not invoices:
            return
        invoices.write({"sent": True})
        invoices.peppol_export_invoice()
