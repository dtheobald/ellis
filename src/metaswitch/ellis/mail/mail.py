# @file mail.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.


import smtplib
import logging
import random
import urllib
import string
from tornado.template import Template
from pkg_resources import resource_string

from metaswitch.ellis import settings

_log = logging.getLogger("ellis.mail")

_template = Template(resource_string(__name__, "forgotpassword.eml"))

def send_recovery_message(urlbase, address, full_name, token):
    """Send a recovery message to the user.

    urlbase - Prefix of URL to insert into email.  Will have
    email=blah&token=blah appended to it.

    address - email address to send message to.

    full_name - full name to address email to.

    token - token to include in email.
    """
    _log.info("Sending recovery message to %s: token is '%s'", address, token)
    
    link = "%semail=%s&token=%s" % (urlbase,
                                    urllib.quote_plus(address),
                                    urllib.quote_plus(token))
    boundary = string.join((random.choice(string.letters) for i in xrange(16)), '')

    message = _template.generate(from_    = settings.EMAIL_RECOVERY_SENDER,
                                 fromname = settings.EMAIL_RECOVERY_SENDER_NAME,
                                 to       = address,
                                 name     = full_name,
                                 link     = link,
                                 signoff  = settings.EMAIL_RECOVERY_SIGNOFF,
                                 boundary = boundary)
    message_bytes = message.encode("utf-8")

    try:
        server = smtplib.SMTP(
            host = settings.SMTP_SMARTHOST,
            port = settings.SMTP_PORT,
            timeout = settings.SMTP_TIMEOUT_SEC)
        server.set_debuglevel(_log.isEnabledFor(logging.DEBUG))
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.ehlo()  # @@@KSW apparently - seems silly to me
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_RECOVERY_SENDER, address, message_bytes)
        server.quit()
    except smtplib.SMTPException as e: # pragma: no cover
        _log.error("Unable to send email to %s via %s/%s/%s: %s", address, 
                   settings.SMTP_SMARTHOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, e)
        raise e
    else:
        _log.info("Sent email to %s", address)
