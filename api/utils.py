def get_uptime(start_time):
    import time
    seconds = int(time.time() - start_time)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
