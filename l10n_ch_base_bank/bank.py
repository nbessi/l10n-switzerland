# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
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
import re
from openerp import models, fields, api, _
from openerp.tools import mod10r


class BankCommon(object):

    def _check_9_pos_postal_num(self, number):
        """
        check if a postal number in format xx-xxxxxx-x is correct,
        return true if it matches the pattern
        and if check sum mod10 is ok
        """
        pattern = r'^[0-9]{2}-[0-9]{1,6}-[0-9]$'
        if not re.search(pattern, number):
            return False
        nums = number.split('-')
        prefix = nums[0]
        num = nums[1].rjust(6, '0')
        checksum = nums[2]
        expected_checksum = mod10r(prefix + num)[-1]
        return expected_checksum == checksum

    def _check_5_pos_postal_num(self, number):
        """
        check if a postal number on 5 positions is correct
        """
        pattern = r'^[0-9]{1,5}$'
        if not re.search(pattern, number):
            return False
        return True


class Bank(models.Model, BankCommon):
    """Inherit res.bank class in order to add swiss specific field"""

    code = fields.Char(string='Code', size=64, help='Internal reference')
    clearing = fields.Char(string='Clearing number', size=64,
        help='Swiss unique bank identifier also used in IBAN number')
    city = fields.Char(string='City', size=128, help="City of the bank")
    ccp = fields.Char(string='CCP', size=64, help="ccp of the bank")

    def _check_ccp_duplication(self, cursor, uid, ids):
        p_acc_obj = self.pool['res.partner.bank']
        for bank in self.browse(cursor, uid, ids):
            p_acc_ids = p_acc_obj.search(cursor, uid, [('bank', '=', bank.id)])
            if p_acc_ids:
                check = p_acc_obj._check_ccp_duplication(
                    cursor,
                    uid,
                    p_acc_ids
                )
                if not check:
                    return False
        return True

    def _check_postal_num(self, cursor, uid, ids):
        """
        validate postal number format
        """
        banks = self.browse(cursor, uid, ids)
        for bank in banks:
            if not bank.ccp:
                continue
            if not (self._check_9_pos_postal_num(bank.ccp) or
                    self._check_5_pos_postal_num(bank.ccp)):
                return False
        return True

    @api.multi
    def name_get(self):
        res = []
        cols = ('bic', 'name', 'street', 'city')
        for bank in self:
            vals = (bank[x] for x in cols if bank[x])
            res.append((bank.id, ' - '.join(vals)))
        return res


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if args is None:
            args = []
        if context is None:
            context = {}
        ids = []
        cols = ('code', 'bic', 'name', 'street', 'city')
        if name:
            for val in name.split(' '):
                for col in cols:
                    tmp_ids = self.search(
                        cursor,
                        uid,
                        [(col, 'ilike', val)] + args,
                        limit=limit
                    )
                    if tmp_ids:
                        ids += tmp_ids
                        break
        # we sort by occurence
        to_ret_ids = list(set(ids))
        to_ret_ids = sorted(
            to_ret_ids,
            key=lambda x: ids.count(x),
            reverse=True
        )

        return self.name_get(cursor, uid, to_ret_ids, context=context)

    _constraints = [
        (_check_postal_num,
         'Please enter a correct postal number. (01-23456-1 or 12345)',
         ['ccp']),

        (_check_ccp_duplication,
         'You can not enter a ccp both on the bank and on an account'
         ' of type BV, BVR',
         ['acc_number', 'bank'])
    ]


class ResPartnerBank(models.Model, BankCommon):
    """
    Inherit res.partner.bank class in order to add swiss specific fields
    and state controls

    """
    _inherit = 'res.partner.bank'

    bvr_adherent_num = fields.Char(
        string='Bank BVR adherent number', size=11,
        help=("Your Bank adherent number to be printed in references of your BVR."
            "This is not a postal account number.")
        )
    acc_number = fields.Char(string='Account/IBAN Number', size=64)
    ccp = fields.Char(string='CCP', related='bank.ccp', store=True, readonly=True)

    @api.model
    def get_account_number(self, bid):
        if isinstance(bid, list):
            bid = bid[0]
        if self.state not in ('bv', 'bvr'):
            return self.acc_number
        if self.bank and self.bank.ccp:
            return self.bank.ccp
        else:
            return self.acc_number

    @api.multi
    def _check_postal_num(self):
        """
        validate postal number format
        """
        for p_bank in self:
            if not p_bank.state in ('bv', 'bvr'):
                continue
            if not p_bank.get_account_number():
                continue
            acc = p_bank.get_account_number()
            if not (
                    self._check_9_pos_postal_num(acc) or
                    self._check_5_pos_postal_num(acc)):
                return False
        return True

    @api.multi
    def _check_ccp_duplication(self):
        """
          Ensure that there is not a ccp in bank and res partner bank
          at same time
        """
        for p_bank in self:
            if not p_bank.state in ('bv', 'bvr'):
                continue
            bank_ccp = p_bank.bank.ccp if p_bank.bank else False
            if not bank_ccp:
                continue
            part_bank_check = (
                self._check_5_pos_postal_num(p_bank.acc_number) or
                self._check_9_pos_postal_num(p_bank.acc_number)
            )
            bank_check = (
                self._check_5_pos_postal_num(p_bank.bank.ccp) or
                self._check_9_pos_postal_num(p_bank.bank.ccp)
            )
            if part_bank_check and bank_check:
                return False
        return True

    _constraints = [
        (_check_postal_num,
         'Please enter a correct postal number. (01-23456-1 or 12345)',
         ['acc_number']),

        (_check_ccp_duplication,
         'You can not enter a ccp both on the bank and on an account'
         ' of type BV, BVR',
         ['acc_number', 'bank'])
    ]

    _sql_constraints = [('bvr_adherent_uniq', 'unique (bvr_adherent_num)',
                         'The BVR adherent number must be unique !')]
