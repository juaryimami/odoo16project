from odoo import models, fields, api, _


class ResumeScreening(models.Model):
   _inherit = "hr.applicant"

   resume_screening = fields.Many2one('cv.completness')
   cv_clarity = fields.Many2one('cv.clarity', string="CV clarity to CV clarity & grammar")
   experience_id = fields.Many2one('applicant.experience',string="Candidate Experience")
   career_pattern = fields.Many2one('career.pattern', string="Career Pattern")
   work_gap = fields.Many2one('work.gap', string="Work Gap")
   career_stablity = fields.Many2one('career.stability', string="Career Stability In Job")
   training_skill = fields.Many2many('training.skill', string="Training & Special Skill")
   education_level = fields.Many2one('education.level', string="Education Level")
   experience_grade = fields.Many2one('experience.grade', string="Experience Grade")

   grade = fields.Float(string="Total Score", compute="_compute_total_score", store = True)
   average = fields.Float(compute="_compute_average")

  

   @api.depends('resume_screening','cv_clarity','experience_id',
                 'career_pattern','work_gap','career_stablity',
                 'training_skill','education_level','experience_grade')
   def _compute_total_score(self):

      for rec in self:

         cv = self.env['cv.completness'].search([('id','=',rec.resume_screening.id)])
         num1=cv.weight if cv else 0
         cl = self.env['cv.clarity'].search([('id', '=', rec.cv_clarity.id)])
         num2 = cl.weight if cl else 0
         candex = self.env['candidate.experience'].search([('id', '=', rec.experience_id.id)])
         num3 = candex.weight if candex else 0
         career = self.env['career.pattern'].search([('id', '=', rec.career_pattern.id)])
         num4 = career.weight if career else 0
         work = self.env['work.gap'].search([('id', '=', rec.work_gap.id)])
         num5 = work.weight if work else 0
         careers = self.env['career.stability'].search([('id', '=', rec.career_stablity.id)])
         num6 = careers.weight if careers else 0
         experience_grade = self.env['experience.grade'].search([('id', '=', rec.experience_grade.id)])
         num9 = experience_grade.weight if experience_grade else 0
         train = self.env['training.skill'].search([('id', 'in', rec.training_skill.ids)])
         num7=0
         for tr in train:
            num7 += tr.weight
         educ = self.env['education.level'].search([('id', '=', rec.education_level.id)])
         num8 = educ.weight
         sum = num1 + num2 + num3 + num4 + num5 + num6 + num7 + num8+num9
         rec.grade = sum

   @api.depends('grade')
   def _compute_average(self):
      for rec in self:
         rec.average = rec.grade / 8


class CvCompletness(models.Model):
   _name = "cv.completness"

   name = fields.Char(string="Name")
   weight = fields.Float()

class CvClarity(models.Model):
   _name = "cv.clarity"

   name = fields.Char(string="Name")
   weight = fields.Float()

class CandidateExperience(models.Model):
   _name = "candidate.experience"

   name = fields.Char(string="Name")
   weight = fields.Float()

class CareerPattern(models.Model):
   _name = "career.pattern"

   name = fields.Char(string="Name")
   weight = fields.Float()

class WorkGap(models.Model):
   _name = "work.gap"

   name = fields.Char(string="Name")
   weight = fields.Float()

class StabilityInJob(models.Model):
   _name = "career.stability"

   name = fields.Char(string="Name")
   weight = fields.Float()

class TrainingSkill(models.Model):
   _name = "training.skill"

   name = fields.Char(string="Name")
   weight = fields.Float()

class EducationalLevel(models.Model):
   _name = "education.level"

   name = fields.Char(string="Name")
   weight = fields.Float()

class ExperienceGrade(models.Model):
   _name = "experience.grade"

   name = fields.Char(string="Name")
   weight = fields.Float()

