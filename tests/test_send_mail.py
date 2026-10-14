import pytest
from kombu.exceptions import OperationalError

from test_mail import flaskbb_tpl_admin_settings_menu
from test_mail.tasks import send_test_mail

SEND_URL = "/test-mail/send"


def test_admin_menu_links_the_send_page_for_admins(request_context, admin_user):
    [link] = flaskbb_tpl_admin_settings_menu(admin_user)

    assert link.endpoint == "test_mail_bp.send_mail"


@pytest.mark.parametrize("member", ["user", "moderator_user", "super_moderator_user", "guest"])
def test_admin_menu_is_empty_for_everyone_else(request_context, default_groups, member, request):
    assert flaskbb_tpl_admin_settings_menu(request.getfixturevalue(member)) == []


def test_send_page_shows_the_mail_config_without_the_password(
    application, client, admin_user, monkeypatch
):
    monkeypatch.setitem(application.config, "MAIL_SERVER", "smtp.example.org")
    monkeypatch.setitem(application.config, "MAIL_PASSWORD", "hunter2")

    resp = client(admin_user).get(SEND_URL)

    assert resp.status_code == 200
    page = resp.get_data(as_text=True)
    assert "smtp.example.org" in page
    assert "********" in page
    assert "hunter2" not in page


def test_send_page_leaves_an_empty_password_empty(application, client, admin_user, monkeypatch):
    monkeypatch.setitem(application.config, "MAIL_PASSWORD", "")

    resp = client(admin_user).get(SEND_URL)

    assert "********" not in resp.get_data(as_text=True)


@pytest.mark.parametrize("member", ["user", "moderator_user", "super_moderator_user"])
def test_send_page_is_forbidden_for_non_admins(client, member, request):
    assert client(request.getfixturevalue(member)).get(SEND_URL).status_code == 403


def test_send_page_is_forbidden_for_guests(client):
    assert client().get(SEND_URL).status_code == 403


def test_sending_mails_the_given_address(client, admin_user, no_csrf, sent_mails):
    resp = client(admin_user).post(SEND_URL, data={"email": "someone@example.org"})

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(SEND_URL)
    [mail] = sent_mails
    assert mail["recipients"] == ["someone@example.org"]
    assert mail["text_body"] == "Test mail sent by test_admin."


def test_sending_without_an_address_shows_the_form_again(client, admin_user, no_csrf, sent_mails):
    resp = client(admin_user).post(SEND_URL, data={"email": ""})

    assert resp.status_code == 200
    assert "Please enter a email address." in resp.get_data(as_text=True)
    assert sent_mails == []


def test_non_admins_cannot_send(client, user, no_csrf, sent_mails):
    resp = client(user).post(SEND_URL, data={"email": "someone@example.org"})

    assert resp.status_code == 403
    assert sent_mails == []


def test_the_task_does_not_track_its_result():
    # a tracked result blocks .delay() for ~20s when the result backend is down
    assert send_test_mail.ignore_result


def test_sending_without_a_broker_mails_in_process(client, admin_user, no_csrf, sent_mails, mocker):
    mocker.patch.object(send_test_mail, "delay", side_effect=OperationalError)

    resp = client(admin_user).post(SEND_URL, data={"email": "someone@example.org"})

    assert resp.status_code == 302
    [mail] = sent_mails
    assert mail["recipients"] == ["someone@example.org"]


def test_a_failed_send_without_a_broker_shows_the_error(client, admin_user, no_csrf, mocker):
    mocker.patch.object(send_test_mail, "delay", side_effect=OperationalError)
    mocker.patch("test_mail.tasks.send_email", side_effect=ConnectionRefusedError("refused"))

    resp = client(admin_user).post(
        SEND_URL, data={"email": "someone@example.org"}, follow_redirects=True
    )

    page = resp.get_data(as_text=True)
    assert "Could not send the mail: refused" in page
    assert "Mail sent to" not in page
