# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import openerp.tests.common as test_common


class TestPaymentSlip(test_common.TransactionCase):

    def setUp(self):
        super(TestPaymentSlip, self).setUp()
        company = self.env.ref('base.main_company')
        self.assertTrue(company)
        partner = self.env.ref('base.main_partner')
        self.assertTrue(partner)
        self.bank = self.env['res.bank'].create(
            {
                'name': 'BCV',
                'ccp': '01-1234-1',
                'bic': '234234',
                'clearing': '234234',
            }
        )
        self.bank_account = self.env['res.partner.bank'].create(
            {
                'partner_id': partner.id,
                'owner_name': partner.name,
                'street':  partner.street,
                'city': partner.city,
                'zip':  partner.zip,
                'state': 'bvr',
                'bank': self.bank.id,
                'bank_name': self.bank.name,
                'bank_bic': self.bank.bic,
                'acc_number': '01-0123-23',
                'bvr_adherent_num': '1234567',
                'print_bank': True,
                'print_account': True,
                'print_partner': True,
            }
        )

    def test_invoice_confirmation(self):
        """Test that confirming an invoice generate slips correctly"""
        invoice = self.env['account.invoice'].create(
            {
                'type': 'out_invoice',
                'partner_id': self.env.ref('base.res_partner_12').id,
                'reference_type': 'none',
                'name': 'A customer invoice',
                'account_id': self.env.ref('account.a_recv').id,
                'type': 'out_invoice',
            }
        )

        self.env['account.invoice.line'].create(
            {
                'product_id': False,
                'quantity': 1,
                'price_unit': 862.50,
                'invoice_id': invoice.id,
                'name': 'product that cost 862.50 all tax included',
            }
        )
        invoice.signal_workflow('invoice_open')
        invoice.refresh()
        self.assertEqual(invoice.amount_total, 862.50)
        for line in invoice.move_id.line_id:
            if line.account_id.type in ('payable', 'receivable'):
                self.assertTrue(line.transaction_ref)
            else:
                self.assertFalse(line.transaction_ref)
        for line in invoice.move_id.line_id:
            slip = self.env['l10n_ch.payment_slip'].search(
                [('move_line_id', '=', line.id)]
            )
            if line.account_id.type in ('payable', 'receivable'):
                self.assertTrue(slip)
                self.assertEqual(slip.amount_total, 862.50)
                self.assertEqual(slip.invoice.id, invoice.id)
            else:
                self.assertFalse(slip)
