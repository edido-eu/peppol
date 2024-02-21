# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged
from odoo_test_helper import FakeModelLoader

from .model import AccountMove


@tagged("post_install", "-at_install")
class TestUBLPaymentModeRequired(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        cls.loader.update_registry((AccountMove,))

        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, force_report_rendering=True
            )
        )
        cls.mode = cls.env.ref("account_payment_mode.payment_mode_outbound_ct1")
        cls.env.user.groups_id |= cls.env.ref("account.group_account_manager")

        cls.AccountMove = cls.env["account.move"]

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test",
            }
        )

        # Instance: company
        cls.company = cls.env.ref("base.main_company")

        # Instance: product
        cls.product = cls.env.ref("product.product_product_4")

        cls.invoice = cls.AccountMove.create(
            {
                "partner_id": cls.partner.id,
                "move_type": "out_invoice",
                "invoice_date": "2019-01-21",
                "date": "2019-01-21",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "test",
                            "price_unit": 10.0,
                            "quantity": 1,
                            "product_id": cls.product.id,
                        }
                    ),
                ],
            }
        )

        cls.invoice.action_post()

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @classmethod
    def _generate_invoice_document(cls, invoice, mode):
        nsmap, ns = cls.env["base.ubl"]._ubl_get_nsmap_namespace(
            "Invoice-2", version="2.1"
        )
        xml_root = etree.Element("Invoice", nsmap=nsmap)
        invoice._ubl_add_payment_means(
            invoice.partner_bank_id,
            mode,
            invoice.invoice_date_due,
            xml_root,
            ns,
            payment_identifier=invoice.payment_reference,
            version="2.1",
        )

    def test_invoice_document_required_false(self):
        self.env.company.ubl_payment_mode_required = True
        with self.assertRaises(UserError) as e:
            self._generate_invoice_document(self.invoice, False)
        self.assertEqual(
            e.exception.args[0], "You must define a payment mode on the invoice"
        )

    def test_invoice_document_not_required(self):
        self._generate_invoice_document(self.invoice, False)

    def test_invoice_document_required(self):
        self.env.company.ubl_payment_mode_required = True
        self._generate_invoice_document(self.invoice, self.mode.sudo())
