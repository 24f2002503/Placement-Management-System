import os
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email
from flask_wtf.file import FileField, FileAllowed
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField(
        'Role',
        choices=[
            ('admin', 'Admin'),
            ('company', 'Company'),
            ('student', 'Student')
        ]
    )
    submit = SubmitField('Login')

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(),Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired()])
    hr_contact = StringField('HR Contact', validators=[Length(max=100)])
    website = StringField('Website', validators=[Length(max=200)])
    overview = TextAreaField('Company Overview')
    submit =SubmitField('Save Company')

class EditCompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[Length(max=100)])
    password = PasswordField('Password')
    hr_contact = StringField('HR Contact', validators=[Length(max=100)])
    website = StringField('Website', validators=[Length(max=200)])
    overview = TextAreaField('Company Overview')
    submit =SubmitField('Edit Company')

class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(),Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired()])
    dept = StringField('Department', validators=[Length(max=100)])
    resume = FileField(
        'Resume (PDF only)',
        validators=[FileAllowed(['pdf'], 'PDF only!')]
    )
    submit =SubmitField('Save Student')

class PlacementDriveForm(FlaskForm):
    drivename = StringField('Drive Name', validators=[DataRequired(), Length(max=100)])
    job_title = StringField('Job Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    eligibility = StringField('Eligibility', validators=[Length(max=200)])
    package = StringField('Package', validators=[Length(max=50)])
    deadline=DateField("Application Deadline", validators=[DataRequired()])
    submit =SubmitField('Create Drive')

class EditStudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(),Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('New Password')
    dept = StringField('Department', validators=[Length(max=100)])

    resume = FileField(
        'Update Resume (PDF only)',
        validators=[FileAllowed(['pdf'], 'PDF files only!')]
    )

    submit =SubmitField('Update Profile')

class ApplicationForm(FlaskForm):
    status = SelectField(
        'Status',
        choices=[
            ('Applied', 'Applied'),
            ('Shortlisted', 'Shortlisted'),
            ('Selected', 'Selected'),
            ('Rejected', 'Rejected')
        ]
    )
    submit = SubmitField('Update Status')

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    overview = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    drives = db.relationship('PlacementDrive', backref='company', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    dept = db.Column(db.String(100))
    resume_path = db.Column(db.String(200))
    is_blacklisted = db.Column(db.Boolean, default=False)
    applications = db.relationship('Application', backref='student', lazy=True)

class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drivename = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String)
    eligibility = db.Column(db.String(200))
    package = db.Column(db.String(50))
    deadline = db.Column(db.Date())
    status = db.Column(db.String(20), default='Open')
    applications = db.relationship('Application', backref='drive', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    date_applied = db.Column(db.Date,default=date.today)
    status = db.Column(db.String(20), default='Applied')
