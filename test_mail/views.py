"""
test_mail.views
~~~~~~~~~~~~~~~

This module contains the views for the test mail Plugin.

:copyright: (c) 2018 by Peter Justin.
:license: BSD License, see LICENSE for more details.
"""

from flask import Blueprint, current_app, flash, redirect, url_for
from flask_babelplus import gettext as _
from flask_login import current_user
from flaskbb.extensions import allows
from flaskbb.utils.helpers import render_template
from flaskbb.utils.requirements import IsAdmin
from kombu.exceptions import OperationalError

from .forms import TestMailForm
from .tasks import send_test_mail

test_mail_bp = Blueprint("test_mail_bp", __name__, template_folder="templates")


def _mail_config():
    return [
        (key, "********" if key == "MAIL_PASSWORD" and value else value)
        for key, value in sorted(current_app.config.items())
        if key.startswith("MAIL_")
    ]


@test_mail_bp.route("/send", methods=["GET", "POST"])
@allows.requires(IsAdmin)
def send_mail():
    form = TestMailForm()
    if form.validate_on_submit():
        try:
            send_test_mail.delay(form.email.data, current_user.username)
        except OperationalError:
            # without a broker, send it in-process to test the mail settings anyway
            try:
                send_test_mail(form.email.data, current_user.username)
            except OSError as e:
                flash(_("Could not send the mail: %(error)s", error=e), "danger")
                return redirect(url_for("test_mail_bp.send_mail"))
        flash(_("Mail sent to %(email)s", email=form.email.data), "success")
        return redirect(url_for("test_mail_bp.send_mail"))
    return render_template("test_mail.html", form=form, mail_config=_mail_config())
