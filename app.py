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

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/')
def index():
    role = session.get('role')
    if role:
        return redirect(url_for(f"{role}_dashboard"))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        role = form.role.data

        user = None
        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['role'] = role
                session['name'] = "Admin"
                return redirect(url_for(f"{role}_dashboard"))
            else:
                flash('Invalid credentials.', 'danger')

        elif role == 'company':
            user = Company.query.filter_by(hr_contact=email).first()
            if user and check_password_hash(user.password, password):

                if user.is_blacklisted:
                    flash('Your account has been blacklisted/deactivated', 'danger')
                    return redirect(url_for('login'))
                if role == 'company' and not user.is_approved:
                    flash(' Your account is pending admin approval.', 'warning') 
                    return redirect(url_for('login'))
                

                session['user_id'] = user.id
                session['role'] = role
                session['name'] = user.name
                session['status'] = user.is_blacklisted
                return redirect(url_for(f"{role}_dashboard"))
            else:
                flash('Invalid credentials.', 'danger')

        elif role == 'student':
            user = Student.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):

                if user.is_blacklisted:
                    flash('Your account has been blacklisted/deactivated', 'danger')
                    return redirect(url_for('login'))
                session['user_id'] = user.id
                session['role'] = role
                session['name'] = user.name
                session['status'] = user.is_blacklisted
                return redirect(url_for(f"{role}_dashboard"))
            else:
                flash('Invalid credentials.', 'danger')

    return render_template('login.html',form=form)

@app.route('/register_company', methods=['GET', 'POST'])
def register_company():
    form=CompanyForm()

    if form.validate_on_submit():
        existing_company = Company.query.filter_by(name=form.name.data).first()

        if existing_company:
            flash('Company already registered.', 'danger')
            return redirect(url_for('register_company'))
        new_company = Company(
            name=form.name.data,
            password=generate_password_hash(form.password.data),
            hr_contact=form.hr_contact.data,
            website=form.website.data,
            overview=form.overview.data,
            is_approved=False,
            is_blacklisted=False
        )

        db.session.add(new_company)
        db.session.commit()

        flash('Company registered successfully. Wait for admin approval.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_company.html', form=form)

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
     form = StudentForm()

     if form.validate_on_submit():
        existing_student = Student.query.filter_by(email=form.email.data).first()

        if existing_student:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register_student'))
        resume_file = form.resume.data
        filename = secure_filename(resume_file.filename)
        filename = f"{form.email.data}_{filename}"

        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        resume_file.save(resume_path)

        new_student = Student(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            dept=form.dept.data,
            resume_path=resume_path,
            is_blacklisted=False
        )

        db.session.add(new_student)
        db.session.commit()

        flash('Student registered successfully.', 'success')
        return redirect(url_for('login'))
    
     return render_template('register_student.html', form=form)

@app.route('/company/dashboard')
def company_dashboard():
       if 'user_id' not in session or session['role'] != 'company' or session['status']:
         return redirect(url_for('login'))

       company_id = session['user_id']

       upcoming_drives = PlacementDrive.query.filter_by(
             company_id=company_id,
             status='Open'
        ).all()
       
       closed_drives = PlacementDrive.query.filter_by(
             company_id=company_id,
             status='Close'
        ).all()
       
       return render_template(
           'company_dashboard.html',
           upcoming_drives=upcoming_drives,
           closed_drives=closed_drives
       )
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student' or session['status']:
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    
    companies = Company.query.filter_by(is_approved=True).all()

    applications = Application.query.filter_by(student_id=student_id).all()

    return render_template(
        'student_dashboard.html',
        companies=companies,
        applications=applications
    )
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    search_query = request.args.get('search')
    
    if search_query:
        companies = Company.query.filter(
            Company.name.ilike(f"%{search_query}%")
        ).all()

        students = Student.query.filter(
            Student.name.ilike(f"%{search_query}%") | (Student.id == search_query)  | (Student.email.ilike(f"%{search_query}%"))
            ).all()

        ongoing_drives = PlacementDrive.query.filter(
            PlacementDrive.drivename.ilike(f"%{search_query}%"),
            PlacementDrive.status == 'Open'
        ).all()

        unapproved_companies= Company.query.filter(
            Company.name.ilike(f"%{search_query}%"),
            Company.is_approved == False
        ).all()
        applications= Application.query.join(Student).join(PlacementDrive).join(Company).filter(
    (Student.name.ilike(f"%{search_query}%")) |
    (Company.name.ilike(f"%{search_query}%"))
        ).all()
    else:
        companies = Company.query.filter_by(is_approved=True).all()
        students = Student.query.all()
        ongoing_drives = PlacementDrive.query.filter_by(status='Open').all()

        unapproved_companies = Company.query.filter_by(is_approved=False).all()
        applications = Application.query.all()

    return render_template(
        'admin_dashboard.html',
        companies=companies,
        students=students,
        unapproved_companies=unapproved_companies,
        ongoing_drives=ongoing_drives,
        applications=applications
    )

@app.route('/admin/company/<int:company_id>/blacklist')
def blacklist_company(company_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    company = Company.query.get_or_404(company_id)
    if not company.is_blacklisted:
        company.is_blacklisted = True

        drives = PlacementDrive.query.filter_by(company_id=company.id).all()
        for drive in drives:
            if drive.status=='Open':
                drive.status = 'Blacklisted'

        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    else:
        company.is_blacklisted = False
        drives = PlacementDrive.query.filter_by(company_id=company.id).all()
        for drive in drives:
            if drive.status=='Blacklisted' and drive.deadline >=date.today():
                drive.status = 'Open'

        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/student/<int:student_id>/blacklist')
def blacklist_student(student_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    student = Student.query.get_or_404(student_id)
    if not student.is_blacklisted:
        student.is_blacklisted = True

        appl=Application.query.filter_by(student_id=student_id).all()
        for a in appl:
            db.session.delete(a)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    else:
        student.is_blacklisted = False

        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/student/<int:company_id>/approve')
def approve_company(company_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    company = Company.query.get_or_404(company_id)
    company.is_approved = True

    db.session.commit()

    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/drive/<int:drive_id>')
def admin_view_drive(drive_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    drive = PlacementDrive.query.get_or_404(drive_id
                                            )
    return render_template('admin_drive_details.html', drive=drive)
    
@app.route('/admin/applications/<int:app_id>')
def admin_view_application(app_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    application = Application.query.get_or_404(app_id)

    return render_template(
        'admin_applications_details.html',
        application=application
    )

@app.route('/company/drive/<int:drive_id>')
def view_drive_applications(drive_id):
    if 'user_id' not in session or session['role'] != 'company' or session['status']:
        return redirect(url_for('login'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = drive.applications

    return render_template(
        'drive_applications.html',
        drive=drive,
        applications=applications
    )

@app.route('/company/drive/<int:drive_id>/close')
def close_drive(drive_id):
    if 'user_id' not in session or session['role'] != 'company' or session['status']:
        return redirect(url_for('login'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)


    if drive.company_id != session['user_id']:
        return redirect(url_for('company_dashboard'))
    
    drive.status= 'Close'
    db.session.commit()

    return redirect(url_for('company_dashboard'))

@app.route('/company/applications/<int:app_id>', methods=['GET', 'POST'])
def review_application(app_id):
    if 'user_id' not in session or session['role'] != 'company' or session['status']:
        return redirect(url_for('login'))
    
    application = Application.query.get_or_404(app_id)
    form = ApplicationForm()

    if form.validate_on_submit():
        application.status = form.status.data
        db.session.commit()
        return redirect(url_for('view_drive_applications', drive_id=application.drive_id))
    
    return render_template(
        'review_application.html',
        application=application,
        form=form
    )

@app.route('/company/create_drive', methods=['GET', 'POST'])
def create_drive():
    if 'user_id' not in session or session['role'] != 'company' or session['status']:
        return redirect(url_for('login'))

    form=PlacementDriveForm()

    if form.validate_on_submit():
        new_drive = PlacementDrive(
        drivename=form.drivename.data,
        job_title=form.job_title.data,
        description=form.description.data,
        eligibility=form.eligibility.data,
        package=form.package.data,
        deadline= form.deadline.data,
        company_id=session['user_id'],
        status='Open'
        )

        db.session.add(new_drive)
        db.session.commit()
    
        return redirect(url_for('company_dashboard'))
    
    return render_template('create_drive.html', form=form)

@app.route('/company/edit_profile', methods=['GET', 'POST'])
def edit_company_profile():
    if 'user_id' not in session or session['role'] != 'company' or session['status']:
        return redirect(url_for('login'))

    company = Company.query.get_or_404(session['user_id'])
    form = EditCompanyForm(obj=company)

    if form.validate_on_submit():

        company.name = form.name.data
        company.hr_contact = form.hr_contact.data
        company.website = form.website.data
        company.overview = form.overview.data


        if form.password.data:
            company.password = generate_password_hash(form.password.data)

        db.session.commit()

        flash('Profile updated successfully', 'success')
        return redirect(url_for('company_dashboard'))
                        
    return render_template('edit_company_profile.html', form=form)

def create_admin():
    admin=Admin.query.filter_by(email="admin@gmail.com").first()
    if not admin:
        adminn=Admin(id=1234, email="admin@gmail.com", password=generate_password_hash("admin252007"))
        db.session.add(adminn)
        db.session.commit()


if __name__ =='__main__':
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)

   