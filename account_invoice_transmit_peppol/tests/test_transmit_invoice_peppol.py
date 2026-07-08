# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mock
from odoo.fields import Command
from odoo.tests import tagged
from requests import Response

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.queue_job.exception import RetryableJobError


@tagged("-at_install", "post_install")
class TestTransmitInvoicePeppol(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("product.product_product_4")
        cls.peppol = cls.env.ref("account_invoice_transmit_peppol.peppol")
        cls.vat_type = cls.env.ref("account_tax_unece.tax_type_vat")
        cls.vat_categ = cls.env.ref("account_tax_unece.tax_categ_s")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Peppol Customer",
                "customer_invoice_transmit_method_id": cls.peppol.id,
            }
        )
        cls.peppol_server = cls.env["peppol.server"].create(
            {
                "name": "Test",
                "account_user": "test",
                "account_password": "test",
            }
        )
        cls.env.company.peppol_server_id = cls.peppol_server

    def _create_invoice(self):
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "test peppol",
                            "price_unit": 100.0,
                            "quantity": 1,
                            "product_id": self.product.id,
                        }
                    )
                ],
            }
        )
        invoice.invoice_line_ids.tax_ids.unece_type_id = self.vat_type
        invoice.invoice_line_ids.tax_ids.unece_categ_id = self.vat_categ
        invoice.action_post()
        return invoice

    def test_temporary_network_failure_is_retryable(self):
        invoice = self._create_invoice()

        response = Response()
        response.status_code = 503
        response._content = b"Service Unavailable"
        with mock.patch("requests.post") as post_mock:
            post_mock.return_value = response
            with self.assertRaisesRegex(
                RetryableJobError,
                "HTTP error 503 sending UBL: Service Unavailable",
            ):
                with self.env.cr.savepoint():
                    invoice._transmit_invoice_by_peppol()
        post_mock.assert_called_once()
