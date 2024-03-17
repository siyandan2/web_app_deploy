from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from Finhub import db
from .models import Profile, Application, Bursary, User, Docs
import os
from datetime import datetime


views = Blueprint('views', __name__)


def is_admin():
    logged_user = User.query.get(int(current_user.id))
    return logged_user.is_admin


@views.route('/')
def index():
    if current_user.is_authenticated:
        if is_admin() == True:
            return redirect(url_for('admin.admin_dashboard'))
    return render_template("index.html", user=current_user)


@views.route('/bursaries')
@login_required
def bursaries():
    if is_admin() == True:
        return redirect(url_for('admin.admin_dashboard'))

    bursary_list = Bursary.query.all()
    bursaries_count = len(bursary_list)
    return render_template("bursaries__list.html", bursaries=bursary_list, user=current_user, bursaries_count=bursaries_count)


@views.route('/bursary-details/<id>')
@login_required
def bursary_details(id):
    if is_admin() == True:
        return redirect(url_for('admin.admin_dashboard'))
    bursary = Bursary.query.get_or_404(int(id))
    current_date = datetime.now().date()
    bursary_closing_date = bursary.closing_date.date()
    status = "Bursary Valid"

    if bursary_closing_date < current_date:
        flash("This bursary is expired!", category='error')
        status = "Bursary Expired"

    return render_template("bursary__details.html", user=current_user, details=bursary, status=status)


@views.route('/submit-application/<ref>', methods=['GET', 'POST'])
@login_required
def submit_application(ref):
    if is_admin() == True:
        return redirect(url_for('admin.admin_dashboard'))
    bursary = Bursary.query.filter_by(reference_number=ref).first()

    current_date = datetime.now().date()
    bursary_closing_date = bursary.closing_date.date()

    if bursary_closing_date < current_date:
        flash("Application for this bursary are not allowed", category='error')
        return redirect('/bursaries')

    if request.method == "POST":

        required_docs = Docs.query.filter_by(user_id=current_user.id).first()

        if not required_docs:
            flash("You haven't uploaded all the required documents, please upload them to proceed!", category='error')
            return redirect(url_for('auth.upload_docs'))

        ref_number = request.form.get('ref')

        bursary = Bursary.query.filter_by(reference_number=ref_number).first()

        already_applied = Application.query.filter_by(
            app_reference_number=bursary.reference_number, user_id=current_user.id)

        if already_applied.count() > 0:
            flash("You have already applied for this bursary", category='error')
            return redirect('/bursaries')

        id_doc = ""
        matric_doc = ""
        academic_doc = ""
        unemployment_doc = ""
        id_doc_link = ""
        matric_doc_link = ""
        academic_doc_link = ""
        unemployment_doc_link = ""

        user_profile = Profile.query.filter_by(user_id=current_user.id).first()

        id_doc_name = secure_filename(
            user_profile.student_number + '_id_doc.pdf')
        matric_doc_name = secure_filename(
            user_profile.student_number + '_matric_doc.pdf')
        academic_doc_name = secure_filename(
            user_profile.student_number + '_academic_doc.pdf')
        unemployment_doc_name = secure_filename(
            user_profile.student_number + '_unemployment_doc.pdf')

        if bursary.certified_id_required:
            id_doc = "Uploaded"
            id_doc_link = id_doc_name
        else:
            id_doc = "Not Required"
            id_doc_link = ""

        if bursary.matric_required:
            matric_doc = "Uploaded"
            matric_doc_link = matric_doc_name
        else:
            matric_doc = "Not Required"
            matric_doc_link = ""

        if bursary.academic_required:
            academic_doc = "Uploaded"
            academic_doc_link = academic_doc_name
        else:
            academic_doc = "Not Required"
            academic_doc_link = ""

        if bursary.unemployment_affidavit:
            unemployment_doc = "Uploaded"
            unemployment_doc_link = unemployment_doc_name
        else:
            unemployment_doc = "Not Required"
            unemployment_doc_link = ""

        cover_letter = request.form.get('cover_letter')

        new_application = Application(
            user_id=current_user.id,
            id_document=id_doc,
            matric_certificate=matric_doc,
            academic_transcript=academic_doc,
            cover_letter=cover_letter,
            unemployed_affidavit=unemployment_doc,
            app_reference_number=ref_number,
            application_status="Submitted",
            is_submitted=True,
            id_doc_link=id_doc_link,
            matric_doc_link=matric_doc_link,
            academic_doc_link=academic_doc_link,
            unemployed_doc_link=unemployment_doc_link
        )

        bursary.number_of_applicants += 1

        db.session.add(new_application)
        db.session.commit()

        flash("Application Submitted Successfully!", category='success')
        return redirect('/application-success')

    return render_template("apply__for__bursary.html", user=current_user, bursary=bursary)


@views.route('/application-success')
@login_required
def application_success():
    if is_admin() == True:
        return redirect(url_for('admin.admin_dashboard'))
    return render_template("application__success.html", user=current_user)


@views.route('/my-applications')
@login_required
def my_applications():
    if is_admin() == True:
        return redirect(url_for('admin.admin_dashboard'))
    return render_template("my__aplications.html", user=current_user)


@views.route('/application-tracking/<id>')
@login_required
def track_application(id):
    if is_admin() == True:
        return redirect(url_for('admin.admin_dashboard'))

    application_details = Application.query.get_or_404(int(id))
    bursary = Bursary.query.filter_by(
        reference_number=application_details.app_reference_number).first()
    if application_details.user_id != current_user.id:
        flash("Access Denied! You can't track other user's applications",
              category='error')
        return redirect('/my-applications')
    return render_template("application__tracking.html", user=current_user, application=application_details, bursary=bursary)
