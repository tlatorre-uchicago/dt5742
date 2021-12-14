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
from .channeldb import ChannelStatusForm, upload_channel_status, get_channels, get_channel_status, get_channel_status_form, get_channel_history, get_pmt_info, get_nominal_settings, get_discriminator_threshold, get_all_thresholds, get_maxed_thresholds, get_gtvalid_lengths, get_pmt_types, pmt_type_description, get_fec_db_history

def nocache(view):
    """
    Flask decorator to hopefully prevent Firefox from caching responses which
    are made very often.

    Example:

        @app.route('/foo')
        @nocache
        def foo():
            # do stuff
            return jsonify(*bar)

    Basic idea from https://gist.github.com/arusahni/9434953.

    Required Headers to prevent major browsers from caching content from
    https://stackoverflow.com/questions/49547.
    """
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return update_wrapper(no_cache, view)

@app.template_filter('timefmt')
def timefmt(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(float(timestamp)))

@app.errorhandler(500)
def internal_error(exception):
    return render_template('500.html'), 500

@app.route('/channel-database')
def channel_database():
    limit = request.args.get("limit", 100, type=int)
    sort_by = request.args.get("sort-by", "timestamp")
    results = get_channels(request.args, limit, sort_by)
    return render_template('channel_database.html', results=results, limit=limit, sort_by=sort_by)

@app.template_filter('channel_status')
def filter_channel_status(row):
    status = []
    if row['pmt_removed']:
        status.append("PMT Removed")
    if row['pmt_reinstalled']:
        status.append("PMT Reinstalled")
    if row['low_occupancy']:
        status.append("Low Occ.")
    if row['zero_occupancy']:
        status.append("Zero Occ.")
    if row['screamer']:
        status.append("Screamer")
    if row['bad_discriminator']:
        status.append("Bad Disc.")
    if row['no_n100']:
        status.append("No N100")
    if row['no_n20']:
        status.append("No N20")
    if row['no_esum']:
        status.append("No ESUM")
    if row['cable_pulled']:
        status.append("Cable pulled")
    if row['bad_cable']:
        status.append("Bad Cable")
    if row['resistor_pulled']:
        status.append("Resistor pulled")
    if row['disable_n100']:
        status.append("Disable N100")
    if row['disable_n20']:
        status.append("Disable N20")
    if row['high_dropout']:
        status.append("High Dropout")
    if row['bad_base_current']:
        status.append("Bad Base Current")
    if row['bad_data']:
        status.append("Bad Data")
    if row['bad_calibration']:
        status.append("Bad Calibration")

    if len(status) == 0:
        return "Perfect!"

    return ", ".join(status)

@app.template_filter('time_from_now')
def time_from_now(dt):
    """
    Returns a human readable string representing the time duration between `dt`
    and now. The output was copied from the moment javascript library.

    See https://momentjs.com/docs/#/displaying/fromnow/
    """
    delta = total_seconds(datetime.now() - dt)

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
    return redirect(url_for('channel-database'))
