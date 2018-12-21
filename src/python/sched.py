# Wrapper function for turning on realtime scheduling.

def realtime(pri=98):
    try:
        import _sched
    except ImportError:
        return  # Ignore

    try:
        print 'Turning on realtime scheduling'
        _sched.mlockall()
        _sched.realtime(pri)
    except:
        print "Must be root to call mlockall() and setscheduler(). Skipping them"
