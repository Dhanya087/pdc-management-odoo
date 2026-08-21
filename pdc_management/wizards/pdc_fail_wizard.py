# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PdcFailWizard(models.TransientModel):
    _name = 'pdc.fail.wizard'
    _description = 'Cancel Cheque'

    cheque_id = fields.Many2one(
        'pdc.cheque',
        string='Cheque',
        required=True,
    )
    cheque_number = fields.Char(related='cheque_id.cheque_number', readonly=True)
    amount = fields.Float(related='cheque_id.amount', readonly=True)
    failure_reason = fields.Text(
        string='Cancellation Reason',
        required=True,
        help='Describe why this cheque is being cancelled (e.g., insufficient funds, signature mismatch).',
    )

    def action_confirm_fail(self):
        self.ensure_one()
        cheque = self.cheque_id
        if cheque.status == 'processed':
            raise UserError(_("Cannot cancel a Processed cheque."))
        cheque.write({
            'status': 'cancelled',
            'failure_reason': self.failure_reason,
        })
        cheque.message_post(
            body=_("Cheque cancelled. Reason: %s") % self.failure_reason,
        )
        return {'type': 'ir.actions.act_window_close'}