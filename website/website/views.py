from __future__ import division, print_function
from . import app
from flask import render_template, jsonify, request, redirect, url_for, flash, make_response
import time
from os.path import join
import json
from .tools import parseiso, total_seconds
from collections import deque, namedtuple
from math import isnan
import os
import sys
import random
from .channeldb import get_modules
from datetime import datetime
import pytz

@app.template_filter('timefmt')
def timefmt(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(float(timestamp)))

@app.errorhandler(500)
def internal_error(exception):
    return render_template('500.html'), 500

@app.route('/module-database')
def module_database():
    limit = request.args.get("limit", 100, type=int)
    sort_by = request.args.get("sort-by", "timestamp")
    results = get_modules(request.args, limit, sort_by)
    return render_template('channel_database.html', results=results, limit=limit, sort_by=sort_by)

@app.template_filter('time_from_now')
def time_from_now(dt):
    """
    Returns a human readable string representing the time duration between `dt`
    and now. The output was copied from the moment javascript library.

    See https://momentjs.com/docs/#/displaying/fromnow/
    """
    print(datetime.now())
    print(dt)
    delta = total_seconds(datetime.now(pytz.timezone('US/Pacific')) - dt)

    if delta < 45:
        return "a few seconds ago"
    elif delta < 90:
        return "a minute ago"
    elif delta <= 44*60:
        return "%i minutes ago" % int(round(delta/60))
    elif delta <= 89*60:
        return "an hour ago"
    elif delta <= 21*3600:
        return "%i hours ago" % int(round(delta/3600))
    elif delta <= 35*3600:
        return "a day ago"
    elif delta <= 25*24*3600:
        return "%i days ago" % int(round(delta/(24*3600)))
    elif delta <= 45*24*3600:
        return "a month ago"
    elif delta <= 319*24*3600:
        return "%i months ago" % int(round(delta/(30*24*3600)))
    elif delta <= 547*24*3600:
        return "a year ago"
    else:
        return "%i years ago" % int(round(delta/(365.25*24*3600)))

@app.route('/channel-status')
def channel_status():
    crate = request.args.get("crate", 0, type=int)
    slot = request.args.get("slot", 0, type=int)
    channel = request.args.get("channel", 0, type=int)
    results = get_channel_history(crate, slot, channel)
    pmt_info = get_pmt_info(crate, slot, channel)
    nominal_settings = get_nominal_settings(crate, slot, channel)
    polling_info = get_most_recent_polling_info(crate, slot, channel)
    discriminator_threshold = get_discriminator_threshold(crate, slot)
    gtvalid_lengths = get_gtvalid_lengths(crate, slot)
    fec_db_history = get_fec_db_history(crate, slot, channel)
    vmon, bad_vmon = get_vmon(crate, slot)
    test_failed = get_penn_daq_tests(crate, slot, channel)
    qhs, qhl, qlx = get_pedestals(crate, slot, channel)
    return render_template('channel_status.html', crate=crate, slot=slot, channel=channel, results=results, pmt_info=pmt_info, nominal_settings=nominal_settings, polling_info=polling_info, discriminator_threshold=discriminator_threshold, gtvalid_lengths=gtvalid_lengths, fec_db_history=fec_db_history, vmon=vmon, bad_vmon=bad_vmon, qhs=qhs, qhl=qhl, qlx=qlx, test_failed=test_failed)

@app.route('/')
def index():
    return redirect(url_for('channel_database'))
