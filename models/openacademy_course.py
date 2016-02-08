
# -*- coding: utf-8 -*-

from openerp import models, fields


class OpenacademyCourse(models.Model):
    """First class in the module."""
    _name = 'openacademy.course'

    name = fields.Char(string="Title", required=True)
    description = fields.Text()
