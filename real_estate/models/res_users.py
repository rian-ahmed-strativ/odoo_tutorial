from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many(
        "estate.property",
        "user_id",
        string="Properties",
        domain=[("state", "in", ["new", "offer_received", "offer_accepted"])],
    )
