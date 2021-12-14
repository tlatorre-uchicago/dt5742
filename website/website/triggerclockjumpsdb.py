from .db import engine_nl
from .detector_state import get_latest_run

def get_clock_jumps(limit, selected_run, run_range_low, run_range_high, gold):
    """
    Returns a list of runs and dictionaries
    specifing the number of clock jump for 
    each run on the 10 and 50MHz clocks
    """
    conn = engine_nl.connect()


    if not selected_run and not run_range_high:
        current_run = get_latest_run()
        result = conn.execute("SELECT DISTINCT ON (run) run "
                              "FROM trigger_clock_jumps WHERE run > %s "
                              "ORDER BY run DESC, timestamp DESC", \
                              (current_run - limit))
        result_online = conn.execute("SELECT DISTINCT ON (run) run, status "
                                     "FROM clock_status WHERE run > %s "
                                     "ORDER BY run DESC", (current_run - limit))
        result_gtids = conn.execute("SELECT DISTINCT ON (run, gtid10, gtid50) "
                              "run, clockjump10, clockjump50 "
                              "FROM trigger_clock_jumps WHERE run > %s "
                              "ORDER BY run DESC, gtid10, gtid50, timestamp DESC", \
                              (current_run - limit))
    elif run_range_high:
        result = conn.execute("SELECT DISTINCT ON (run) run "
                              "FROM trigger_clock_jumps WHERE run >= %s "
                              "AND run <= %s "
                              "ORDER BY run DESC, timestamp DESC", \
                              (run_range_low, run_range_high))
        result_online = conn.execute("SELECT DISTINCT ON (run) run, status "
                                     "FROM clock_status WHERE run >= %s AND run <= %s "
                                     "ORDER BY run DESC", (run_range_low, run_range_high))
        result_gtids = conn.execute("SELECT DISTINCT ON (run, gtid10, gtid50) "
                              "run, clockjump10, clockjump50 "
                              "FROM trigger_clock_jumps WHERE run >= %s AND run <= %s "
                              "ORDER BY run DESC, gtid10, gtid50, timestamp DESC", \
                              (run_range_low, run_range_high))
    else:
        result = conn.execute("SELECT DISTINCT ON (run) run "
                              "FROM trigger_clock_jumps WHERE run = %s "
                              "ORDER BY run DESC, timestamp DESC", \
                              (selected_run))
        result_online = conn.execute("SELECT DISTINCT ON (run) run, status "
                                     "FROM clock_status WHERE run = %s "
                                     "ORDER BY run DESC", (selected_run))
        result_gtids = conn.execute("SELECT DISTINCT ON (run, gtid10, gtid50) "
                              "run, clockjump10, clockjump50 "
                              "FROM trigger_clock_jumps WHERE run = %s "
                              "ORDER BY run DESC, gtid10, gtid50, timestamp DESC", \
                              (selected_run))

    rows = result.fetchall()

    runs = []
    njump10 = {}
    njump50 = {}

    for run in rows:
        if gold != 0 and run[0] not in gold:
            continue
        runs.append(run[0])
        njump10[run[0]] = 0
        njump50[run[0]] = 0

    rows = result_online.fetchall()

    clock_offline = {}
    for run, status in rows:
        if gold != 0 and run not in gold:
            continue
        clock_offline[run] = status

    rows = result_gtids.fetchall()

    for run, jump10, jump50 in rows:
        if gold != 0 and run not in gold:
            continue
        if jump10:
            njump10[run] +=1 
        if jump50:
            njump50[run] +=1

    return runs, njump10, njump50, clock_offline


def get_clock_jumps_by_run(run):
    """
    Get the clock jump size (clock ticks), 
    the correction size (clock ticks),
    and the GTID of each clock jump
    """
    conn = engine_nl.connect()

    result = conn.execute("SELECT DISTINCT ON (run, gtid10, gtid50) "
                          "clockjump10, clockfix10, gtid10, "
                          "clockjump50, clockfix50, gtid50 "
                          "FROM trigger_clock_jumps WHERE run = %i "
                          "ORDER BY run DESC, gtid10, gtid50, timestamp DESC" \
                          % int(run))

    rows = result.fetchall()

    data10 = []
    data50 = []

    for clockjump10, clockfix10, gtid10, clockjump50, clockfix50, gtid50 in rows:
        if clockjump10:
            # Convert to s for display
            clockjump10 = (clockjump10*100)*1e-9
            # Convert to ns for display
            clockfix10 = (clockfix10)*100*1e-3
            data10.append((clockjump10,clockfix10,gtid10))
        if clockjump50:
            # Convert to s for display
            clockjump50 = (clockjump50*20)*1e-9
            # Convert to us for display
            clockfix50 = (clockfix50)*20*1e-3
            data50.append((clockjump50,clockfix50,gtid50))

    return data10, data50

