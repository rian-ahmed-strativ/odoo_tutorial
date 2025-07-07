from odoo import models, fields

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Real Estate Property Tag"
    _order = "sequence, name" 

    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string="Color")
    sequence = fields.Integer(string="Sequence", default=10)

    _sql_constraints = [
        ('unique_tag_name', 'UNIQUE(name)', 'The tag name must be unique.')
    ]