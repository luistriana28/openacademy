
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Course(models.Model):
    _name = 'openacademy.course'
    _description = "OpenAcademy Courses"

    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    phone = fields.Text(string="Telefono")
    responsible_id = fields.Many2one(
        'res.users', ondelete='set null',
        string="Responsible", index=True)
    session_ids = fields.One2many(
        'openacademy.session', 'course_id', string="Sessions")
    _sql_constraints = [
        # ('name_description_check',
        #  'CHECK(name != description)',
        #  "The title of the course should not be the description"),
        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
         ]

    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    @api.constrains('name', 'description')
    def _check_name_description_check(self):
        for record in self:
            if record.name == record.description:
                raise ValidationError(
                    'El título no puede ser igual a la descripción')


class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    instructor_id = fields.Many2one(
        'res.partner', string="Instructor",
        domain=['|', ('instructor', '=', True), (
            'category_id.name', 'ilike', "Teacher")])
    course_id = fields.Many2one(
        'openacademy.course',
        ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(
        string="End Date", store=True,
        compute='_compute_get_end_date', inverse='_compute_set_end_date')
    attendees_count = fields.Integer(
        string="Attendees count",
        compute='_compute_get_attendees_count', store=True)
    color = fields.Integer()

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for record in self:
            if not record.seats:
                record.taken_seats = 0.0
            else:
                record.taken_seats = 100.0 * len(
                    record.attendee_ids) / record.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': ("The number of available"
                                " seats may not be negative"),
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    'message': "Increase seats or remove excess attendees",
                },
            }

    @api.depends('start_date', 'duration')
    def _compute_get_end_date(self):
        for record in self:
            if not (record.start_date and record.duration):
                record.end_date = record.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(days=record.duration, seconds=-1)
            record.end_date = record.start_date + duration

    def _compute_set_end_date(self):
        for record in self:
            if not (record.start_date and record.end_date):
                continue

            # Compute the difference between dates, but:
            # Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            record.duration = (record.end_date - record.start_date).days + 1

    @api.depends('attendee_ids')
    def _compute_get_attendees_count(self):
        for record in self:
            record.attendees_count = len(record.attendee_ids)

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for record in self:
            if record.instructor_id in record.attendee_ids:
                raise ValidationError(
                    "A session's instructor can't be an attendee")
