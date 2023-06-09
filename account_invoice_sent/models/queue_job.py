# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models


class QueueJob(models.Model):
    _inherit = "queue.job"

    @api.multi
    def related_action_open_invoice(self):
        """Open a form view with the invoices of the job.

        Use customer/supplier view depending of the type of the invoice.
        """
        self.ensure_one()
        model_name = self.model_name
        records = self.env[model_name].browse(self.record_ids).exists()
        if not records:
            return None

        action = {
            "name": _("Related Record"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": records._name,
        }

        if all(
            invoice_type in ("out_invoice", "out_refund")
            for invoice_type in records.mapped("type")
        ):
            form_xmlid = "account.invoice_form"
            tree_xmlid = "account.invoice_tree"
        else:
            form_xmlid = "account.invoice_supplier_form"
            tree_xmlid = "account.invoice_supplier_tree"
        form_view_id = self.env.ref(form_xmlid).id
        tree_view_id = self.env.ref(tree_xmlid).id

        if len(records) == 1:
            action.update({"res_id": records.id, "view_id": form_view_id})
            action["res_id"] = records.id
        else:
            action.update(
                {
                    "name": _("Related Records"),
                    "view_mode": "tree,form",
                    "domain": [("id", "in", records.ids)],
                    "views": [(tree_view_id, "tree"), (form_view_id, "form")],
                }
            )
        return action
