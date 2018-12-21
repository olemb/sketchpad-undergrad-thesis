#!/usr/local/bin/python

"""
GUI

Run as
PA_MIN_LATENCY_MSEC=50 python record.py
or maybe even
PA_MIN_LATENCY_MSEC=10 python record.py


Todo:

- pause/resume audio when doing file operations?
- "echo input" option in the recorder?
"""

import Tkinter
import os
import sys
import LevelGraph
import LayerDisplay
import tkFileDialog
import tkMessageBox
import audioop
import time

import Recorder

load_save_filetypes = [('WAVE files', '*.wav'),
                       ('All files', '*')]

about_text = """Record
Ole Martin Bjørndalen
olemb@stud.cs.uit.no
http://www.cs.uit.no/~olemb/"""

def format_time(secs):
    min = int(secs / 60)
    sec = int(secs % 60)
    rem = int(secs % 1.0 * 100)
    
    return '%02d:%02d.%02d' % (min, sec, rem)

def every(tk, msec, func, *args, **kw):
    def wrapper():
        func(*args, **kw)
        tk.after(msec, wrapper)
    wrapper()

class PeakMeter:
    """Fallrate is given in units per second"""
    
    def __init__(self, fallrate=1):
        self.fallrate = fallrate
        self.peak = 0.0
        self.last_update = time.time()

    def update(self, value):
        now = time.time()
        dtime = now - self.last_update

        self.peak = self.peak - (dtime * self.fallrate)
        if self.peak < 0:
            self.peak = 0
        self.last_update = now
        
        if value > self.peak:
            self.peak = value

    def get_string(self, width):
        # Note: the value is rounded, not truncated.
        bars = '|' * int(round(self.peak * width))
        bars = bars[:width]
        return bars.ljust(width)

class RecorderGUI:
    def __init__(self):
        self.rec = Recorder.Recorder()  # with default params
        self.make_gui()

        every(self.tk, 100, self.update_display)

    #
    # GUI
    #
        
    def make_gui(self):
        self.tk = Tkinter.Tk()
        self.tk.protocol("WM_DELETE_WINDOW", self.quit)

        menu = Tkinter.Menu(self.tk)
        self.tk.config(menu=menu)

        # Make file menu
        filemenu = Tkinter.Menu(menu)
        menu.add_cascade(label='File', menu=filemenu, underline=0)
        filemenu.add_command(label='New', command=self.new, underline=0, accelerator='Ctrl+N')
        filemenu.add_command(label='Open...', command=self.open, underline=0, accelerator='Ctrl+O')
        filemenu.add_command(label='Save', command=self.save, underline=0, accelerator='Ctrl+S')
        filemenu.add_command(label='Save As...', command=self.save_as, underline=5)
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.quit, underline=1)


        self.tk.bind('<Control-n>', lambda x: self.new())
        self.tk.bind('<Control-o>', lambda x: self.open())
        self.tk.bind('<Control-s>', lambda x: self.save())

        # Make help menu
        helpmenu = Tkinter.Menu(menu)
        menu.add_cascade(label='Help', menu=helpmenu, underline=0)
        helpmenu.add_command(label='About...', command=self.about, underline=0)


        top = Tkinter.Frame(self.tk)
        top.pack(side='top', fill='y')

        #self.peak_meter = PeakMeter()
        #self.peak_canvas = Tkinter.Canvas(left, width=16, height=100, bd=2, relief='sunken')
        #self.peak_canvas.pack(side='top')
        #self.peak_canvas.create_rectangle(0, 0, 0, 0, fill='blue', tag='peak')
        
        self.level_graph = LevelGraph.LevelGraph(top, self.rec.params, 400, 100)
        self.level_graph.pack(side='top')



        bottom = Tkinter.Frame(self.tk)
        bottom.pack(side='top')

        self.layer_display = LayerDisplay.LayerDisplay(bottom,
                                                       self.rec,
                                                       width=400, height=100)
        self.layer_display.pack(side='top')

        self.status_display = Tkinter.Label(bottom)
        self.status_display.pack(side='top')


        butframe = Tkinter.Frame(bottom)
        butframe.pack(side='top')

        but = Tkinter.Button(butframe, text='Record', command=self.record,
                             fg='white', bg='red')
        but.pack(side='left')

        but = Tkinter.Button(butframe, text='Stop', command=self.stop)
        but.pack(side='left')

        but = Tkinter.Button(butframe, text='Play', command=self.play,
                             fg='white', bg='#007700')
        but.pack(side='left')

        but = Tkinter.Button(butframe, text='Undo', command=self.undo,
                             state='disabled')
        but.pack(side='left')
        self.undo_button = but

        
        #self.bind_otto_keys()
        self.bind_olemb_keys()

        self.update_gui_state()

    def bind_otto_keys(self):
        "Otto's keybindings"

        def undo(event):
            self.undo()

        def rec(event):
            if self.recorder.state == 'recording':
                self.stop()
            else:
                self.record()

        def play(event):
            if self.recorder.state == 'playing':
                self.stop()
            else:
                self.play()

        self.tk.bind('<KeyPress-BackSpace>', undo)
        self.tk.bind('<KeyPress-Return>', rec)
        self.tk.bind('<KeyPress-space>', play)
        self.tk.bind('<ButtonPress-2>', play)

    def bind_olemb_keys(self):
        "My keybindings"

        def play_and_stop_toggle(event):
            if self.rec.mode == 'stopped':
                self.play()
            else:
                self.stop()

        def record(event):
            self.record()

        def play(event):
            self.play()

        def stop(event):
            self.stop()

        def undo(event):
            self.undo()

        def record_somewhere(event):
            self.record(100)
            
        #self.tk.bind('<KeyPress-Return>', record)
        #self.tk.bind('<KeyPress-BackSpace>', undo)
        #self.tk.bind('<KeyPress-space>', play_and_stop_toggle)

        self.tk.bind('<KeyPress-r>', record)
        self.tk.bind('<KeyPress-u>', undo)
        self.tk.bind('<KeyPress-BackSpace>', undo)
        self.tk.bind('<KeyPress-p>', play)
        self.tk.bind('<KeyPress-space>', stop)

    #
    # GUI updates
    #

    def update_gui_state(self):
        # Update window title
        title = 'Record'
        filename = self.rec.filename
        if filename != None:
            title =  '%s - %s' % (os.path.basename(filename), title)
        self.tk.title(title)

        # Update state of the undo button
        if self.rec.get_undoable():
            self.undo_button['state'] = 'normal'
        else:
            self.undo_button['state'] = 'disabled'

    def update_display(self):
        secs = self.rec.get_time()
        total = self.rec.get_total()

        text = '%s at %s of %s' % (self.rec.mode,
                                     format_time(secs), format_time(total))

        # text += (' (%d)' % self.rec.changes)

        if self.rec.changes > 0:
            text += ' *'

        self.status_display['text'] = text

    def save_recording(self, filename=None):
        "Save recording. Ask user for filename if filename is false."

        self.stop()
        # self.pause_audio()

        if filename == None or not self.rec.filename:
            filename = tkFileDialog.asksaveasfilename(filetypes=load_save_filetypes)
        
        if filename:
            try:
                self.rec.save(filename)
            except (IOError, wave.Error), msg:
                tkMessageBox.showerror(title='Save failed', message=msg)
            else:
                self.update_gui_state()

        # self.resume_audio()

    #
    # Commands
    #
    def undo(self, pos=0):
        self.rec.undo(pos)
        self.layer_display.undo()
        self.update_gui_state()

    def record(self, pos=0):
        self.rec.record(pos)
        self.layer_display.record()
        self.update_gui_state()

    def play(self, pos=0):
        self.rec.play(pos)

    def stop(self, pos=0):
        self.rec.stop()

    def new(self):
        self.rec.new()
        self.layer_display.clear()
        self.update_gui_state()

    def open(self):
        self.rec.stop()
        # self.pause_audio()

        filename = tkFileDialog.askopenfilename(filetypes=load_save_filetypes)
        if filename:
            try:
                self.rec.load(filename)
            except (IOError, wave.Error), msg:
                tkMessageBox.showerror(title='Open failed', message=msg)
            else:
                self.layer_display.file_loaded()
                self.update_gui_state()
        # self.resume_audio()

    def save_as(self):
        self.save_recording(None)

    def save(self):
        self.save_recording(self.rec.filename)

    def quit(self):
        self.stop()
        self.done = True

    def about(self):
        #self.pause_audio()
        tkMessageBox.showinfo('About', about_text)
        #self.resume_audio()

    def update_peak_meter(self):
        p = self.rec.params
        sum = audioop.add(self.rec.input, self.rec.output, p.sampwidth)
        maxval = audioop.max(sum, p.sampwidth) / float(p.maxval)
        self.peak_meter.update(maxval)

        w = int(self.peak_canvas['width'])
        h = int(self.peak_canvas['height'])

        self.peak_canvas.coords('peak', 0, h, w, h-(h*self.peak_meter.peak))

    #
    # Main loop
    #
    def mainloop(self):
        self.done = 0
        sampwidth = self.rec.params.sampwidth
        while not self.done:
            self.tk.update()
            self.rec.update()
            self.layer_display.update()

            #self.update_peak_meter()
            self.level_graph.feed(self.rec.input, self.rec.output)
        self.tk.destroy()

varname = 'PA_MIN_LATENCY_MSEC'

if os.getenv(varname) == None:
    env = {}
    env.update(os.environ)
    env[varname] = '50'
    os.execvpe(sys.executable, [sys.executable] + sys.argv, env)
else:
    gui = RecorderGUI()
    gui.mainloop()
