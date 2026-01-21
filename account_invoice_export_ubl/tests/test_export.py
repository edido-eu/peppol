# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

import mock
from odoo.addons.base.tests.common import BaseCommon
from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from requests import Response


@tagged("-at-install", "post-install")
class TestExportUbl(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.vat_type = cls.env.ref("account_tax_unece.tax_type_vat")
        cls.vat_categ = cls.env.ref("account_tax_unece.tax_categ_s")

        cls.peppol_server = cls.env["peppol.server"].create(
            {
                "name": "Test",
                "account_user": "test",
                "account_password": "test",
            }
        )
        cls.env.company.peppol_server_id = cls.peppol_server

    def test_export(self):
        with Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.partner_id = self.partner
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
        invoice = invoice_form.save()

        # Set the tax UNECE category
        invoice.invoice_line_ids.tax_ids.unece_type_id = self.vat_type
        invoice.invoice_line_ids.tax_ids.unece_categ_id = self.vat_categ
        invoice._post()
        history_ids = self.peppol_server.history_ids
        response_200 = Response()
        response_200.status_code = 200
        with mock.patch("requests.post") as post_mock:
            post_mock.return_value = response_200
            invoice.peppol_export_invoice()
        self.assertTrue(invoice.is_move_sent)
        self.assertTrue(invoice.invoice_exported)
        self.assertFalse(invoice.invoice_export_confirmed)

        new_history = self.peppol_server.history_ids - history_ids
        self.assertEqual(1, len(new_history))
        # check status
        with mock.patch("requests.post") as post_mock:
            post_mock.return_value = mock.Mock()
            post_mock.return_value.status_code = 200
            post_mock.return_value.text = json.dumps(
                {"status": {new_history.md5: True}}
            )
            self.peppol_server.check_status()
        self.assertTrue(invoice.is_move_sent)
        self.assertTrue(invoice.invoice_export_confirmed)

    def test_export_error(self):
        with Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.partner_id = self.partner
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
        invoice = invoice_form.save()

        # Set the tax UNECE category
        invoice.invoice_line_ids.tax_ids.unece_type_id = self.vat_type
        invoice.invoice_line_ids.tax_ids.unece_categ_id = self.vat_categ
        invoice._post()

        response_400 = Response()
        response_400.status_code = 400
        with mock.patch("requests.post") as post_mock, self.assertRaises(UserError):
            post_mock.return_value = response_400
            invoice.peppol_export_invoice()
        self.assertFalse(invoice.is_move_sent)

    def test_status_error(self):
        with Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.partner_id = self.partner
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
        invoice = invoice_form.save()

        # Set the tax UNECE category
        invoice.invoice_line_ids.tax_ids.unece_type_id = self.vat_type
        invoice.invoice_line_ids.tax_ids.unece_categ_id = self.vat_categ
        invoice._post()
        history_ids = self.peppol_server.history_ids
        response_200 = Response()
        response_200.status_code = 200
        with mock.patch("requests.post") as post_mock:
            post_mock.return_value = response_200
            invoice.peppol_export_invoice()
        self.assertTrue(invoice.is_move_sent)
        self.assertFalse(invoice.invoice_export_confirmed)

        new_history = self.peppol_server.history_ids - history_ids
        self.assertEqual(1, len(new_history))
        # check status
        with mock.patch("requests.post") as post_mock, self.assertRaises(UserError):
            post_mock.return_value = mock.Mock()
            post_mock.return_value.status_code = 400
            self.peppol_server.check_status()
        self.assertTrue(invoice.is_move_sent)
        self.assertFalse(invoice.invoice_export_confirmed)
