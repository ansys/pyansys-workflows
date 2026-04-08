
log_widget = None
tk_master = None

def init_logger(master, widget):
    global tk_master, log_widget
    tk_master = master
    log_widget = widget

def log_message(msg):
    if log_widget is None:
        return
    log_widget.config(state='normal')
    log_widget.insert('end', msg + "\n")
    log_widget.config(state='disabled')
    log_widget.see('end')
    log_widget.update_idletasks()

def log_progress_inline(percent):
    if log_widget is None:
        return

    bar_len = 40
    filled = int(bar_len * percent / 100)
    bar = "#" * filled + "-" * (bar_len - filled)
    text = f"[{bar}] {percent:.1f}%"

    log_widget.config(state='normal')

    # delete previous progress line
    log_widget.delete("end-2l", "end-1l")
    log_widget.insert('end', text + "\n")

    log_widget.config(state='disabled')
    log_widget.see('end')
    log_widget.update_idletasks()

def force_update():
    if tk_master:
        tk_master.update()
