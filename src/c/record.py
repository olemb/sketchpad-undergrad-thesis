"""
Todo:
  - self.bufsize in LayerDisplay and Recorder should not be number of seconds
  - correct graphics after load (stored segment)
  - implement load and save (and quit)

  - if you load a file, and save it to another file, the two files differ. Why?
    (There is something wrong with the size in the header.)
  - Busy pointer while loading and saving (requires Pmw?)
  - "There's some stuff that you haven't saved" is not a good message.
  - Add clear() to record.c and _record.c
  - Error checking!
  - "Are you sure?" when you close the window and there are unsaved changes.
"""

from __future__ import nested_scopes
from Tkinter import *
import tkFileDialog
import tkMessageBox
import sys
import os

import _record

STOPPED = 0
PLAYING = 1
RECORDING = 3

SAMPLE_RATE = 44100
NUM_CHANS = 2

# Use a class for namespace.
# I should replace it with a config file.
class Config:
    pass
config = Config()

all_off = 0
all_on = 1

if all_off:
    config.show_peak_meters = 0
    config.show_segment_display = 0

    # Hiding a control will also disable the keyboard shortcut
    config.show_half_speed_control = 0
    config.show_monitor_input_control = 0
    config.show_undo_button = 0
    config.show_top_level_control = 0
    config.show_status_display = 0
    config.complex_status_display = 0
    config.show_tickline = 1
    
    config.layer_display_width = 400
    config.max_visible_layers = 16
if all_on:
    config.show_peak_meters = 1
    config.show_segment_display = 0

    # Hiding a control will also disable the keyboard shortcut
    config.show_half_speed_control = 0
    config.show_monitor_input_control = 1
    config.show_undo_button = 1
    config.show_top_level_control = 1
    config.show_status_display = 1
    config.complex_status_display = 0
    config.show_tickline = 1
    
    config.layer_display_width = 400
    config.max_visible_layers = 16


def format_pos(pos):
    sec = pos / SAMPLE_RATE / NUM_CHANS
    min = sec / 60
    sec = sec % 60
    return '%02d:%02d' % (min, sec)


class LayerDisplay:
    def __init__(self, parent, width, layer_height, bufsize):
        self.displacement = 4  # Use an int for accuracy
        self.max_layers = config.max_visible_layers
        self.stored_layers = []
        self.bufsize = bufsize
        self.width = width

        self.height = layer_height + (self.displacement * (self.max_layers-1)) # Room for max_layers layers
        if config.show_tickline:
            self.tickline_height = 10
            self.height += self.tickline_height

        self.canvas = Canvas(parent, width=width, height=self.height, borderwidth=1, relief=SUNKEN)

        if config.show_tickline:
            self.draw_tickline()

        self.width = width
        self.layer_height = layer_height
        #self.height = layer_height
        self.top_rect = None
        self.pos_rect = self.canvas.create_rectangle(0, 0, 0, self.height,
                                                     fill='white', outline='white')
        self.bufsize = bufsize

    def pack(self, *args, **kw):
        return self.canvas.pack(*args, **kw)

    def draw_tickline(self):
        self.canvas.delete('ticks')

        secs = float(self.bufsize)
        mins = (secs / 60.0)
        h = self.tickline_height
        y = self.height

        # Draw minute ticks
        dist = float(self.width) / mins
        for i in range(mins+1):
            x = i * dist
            self.canvas.create_line(x, y, x, y-h, fill='black', tag='ticks')

        # Draw second ticks
        dist = float(self.width) / secs
        if dist > 2:
            for i in range(secs+1):
                x = i * dist
                self.canvas.create_line(x, y-h/2, x, y-h, fill='black', tag='ticks')

        # Show available recording time
        total = format_pos(self.bufsize*SAMPLE_RATE*NUM_CHANS)
        self.canvas.create_text(self.width, y-self.tickline_height, anchor='se', text=total)

    def _scale_pos(self, pos):
        #margin = 2
        margin = 0
        width = self.width - margin * 2
        return margin + pos / float(self.bufsize*SAMPLE_RATE*2) * (width)
    
    def discard_layer(self):
        if self.top_rect:
            self.canvas.delete(self.top_rect)
            self.top_rect = None
            
    def keep_layer(self):
        if self.top_rect:
            self.canvas.itemconfigure(self.top_rect, fill='lightblue')

            # Push everything down a bit
            #self.height += self.displacement
            #self.canvas['height'] = self.height
            self.canvas.move('layers', 0, self.displacement)

            self.stored_layers.append(self.top_rect)
            if len(self.stored_layers) > self.max_layers-1:
                # Combine the two lowest layers to make room for new ones
                [below, above] = map(self.canvas.coords, self.stored_layers[:2])
                x1 = min(above[0], below[0])
                x2 = max(above[2], below[2])
                y1 = above[1]
                y2 = above[3]
                self.canvas.coords(self.stored_layers[1], x1, y1, x2, y2)
                # I'm not sure how to represent the combination
                self.canvas.itemconfigure(self.stored_layers[1], stipple='gray25')
                self.canvas.delete(self.stored_layers[0])
                del self.stored_layers[0]

    def new_layer(self, start=0):
        self.keep_layer()
        
        # Add the new layer
        start = self._scale_pos(start)
        self.top_rect = self.canvas.create_rectangle(start,
                                                     0,
                                                     start,
                                                     self.layer_height,
                                                     fill='blue',
                                                     tag='layers')
        self.canvas.tkraise(self.pos_rect)
        
    def _update_cursor(self, pos):
        self.canvas.coords(self.pos_rect, pos, 0, pos, self.height)        

    def update(self, pos, start, end):
        [pos, start, end] = map(self._scale_pos, [pos, start, end])
        if self.top_rect:
            self.canvas.coords(self.top_rect,
                               start,
                               0,
                               end,
                               self.layer_height)
        self._update_cursor(pos)

    def clear(self):
        self.canvas.delete('layers')

    def reset(self, used_start, used_end):
        "Called after loading a file"

        # Grr. Duplicate code here because Tkinter ignores canvas.move()
        # outside of tk.mainloop(). Maybe I could use tk.doonce() (or whatever it is called)
        [start, end] = map(self._scale_pos, [used_start, used_end])
        rect = self.canvas.create_rectangle(start,
                                            0,
                                            end,
                                            self.layer_height,
                                            fill='lightblue',
                                            stipple='gray25',
                                            tag='layers')

        # Push everything down a bit
        #self.height += self.displacement
        #self.canvas['height'] = self.height
        self.canvas.move('layers', 0, self.displacement)
        self.stored_layers.append(rect)
        self.canvas.tkraise(self.pos_rect)

class SegmentDisplay(LayerDisplay):
    def __init__(self, *args, **kw):
        LayerDisplay.__init__(self, *args, **kw)
        self.rects = []

    def update(self, pos, segments):
        while len(segments) < len(self.rects):
            rect = self.rects.pop()
            self.canvas.delete(rect)

        while len(segments) > len(self.rects):
            y1 = self.displacement * len(self.rects)
            y2 = y1 + self.layer_height
            self.rects.append(self.canvas.create_rectangle(0, y1, 0, y2, fill='yellow'))
        for ((start, end, level), rect) in zip(segments, self.rects):
            (old_x1, y1, old_x2, y2) = self.canvas.coords(rect)
            [x1, x2] = map(self._scale_pos, [start, end])
            self.canvas.coords(rect, x1, y1, x2, y2)
            
        #self._update_cursor(self._scale_pos(pos))


class PeakMeter:
    def __init__(self, parent, width, height):
        self.width = width
        self.height = height
        self.canvas = Canvas(parent, width=width, height=height, borderwidth=1, relief=SUNKEN)
        self.rect = self.canvas.create_rectangle(0, 0, 0, 0, fill='blue')
        self.update(0)

    def update(self, value):
        height = value * self.height
        self.canvas.coords(self.rect, 0, self.height, self.width, self.height-height)

    def pack(self, *args, **kw):
        self.canvas.pack(*args, **kw)

class Toggle:
    def __init__(self, parent, label, command, value=0):
        self.label = label
        self.command = command
        self.var = IntVar()
        self.check = Checkbutton(parent, variable=self.var, text=label, command=self._adjust)

        # variable=s.active,

    def _adjust(self):
        self.command(self.get())

    def set(self, value):
        self.var.set(value)
        # We have to call the command here because Tkinter
        # only calls it when you click on the button. This 
        # is inconsistent. The Scale calls its command when
        # you set its value. The Checkbutton should do the
        # same.
        self.command(value)

    def get(self):
        return int(self.var.get())

    def toggle(self):
        self.set(not self.get())

    def pack(self, *args, **kw):
        self.check.pack(*args, **kw)

class LevelControl:
    def __init__(self, parent, command, default=1):
        self.default = default
        self.value = default
        self.command = command
        self.state = 'active'

        self.max_value = 10
        
        self.scale = Scale(parent, from_=0, to=self.max_value,
                           orient=HORIZONTAL,
                           length="1i",
                           resolution="0.01",
                           #label="Level",
                           command=self._set)
        self.scale.set(1)

    def __setitem__(self, key, val):
        self.scale[key] = val

    def _set(self, new_value):
        new_value = float(new_value)
        # Test here, because Tkinter sends update events
        # every the mouse move, even when the slider didn't move!
        if new_value != self.value:
            self.command(new_value)
            self.value = new_value

    def set(self, new_value):
        self.scale.set(new_value)

    def get(self):
        return self.value
            
    def adjust(self, adjustment):
        new_value = self.get() + adjustment
        if new_value < 0:
            new_value = 0
        elif new_value > self.max_value:
            new_value = self.max_value
        self.set(new_value)

    def reset(self):        
        self.value = self.default
        # You can't set the value of a scale while it's disabled.
        # Why not? Beats me.
        if self.scale['state'] == 'disabled':
            self.scale['state'] = 'active'
            self.scale.set(self.default)
            self.scale['state'] = 'disabled'
        else:
            self.scale.set(self.default)

    def pack(self, *args, **kw):
        self.scale.pack(*args, **kw)

class Recorder:
    def __init__(self, bufsize):
        self.bufsize = bufsize
        _record.init(self.bufsize)

        self.filename = None
        self.top_layer_exists = 0

        self.open_window()
        self.set_modified(0)

    def set_filename(self, filename=None):
        self.filename = filename
        if filename:
            filename = os.path.basename(filename)
        else:
            filename = 'Untitled'
        self.tk.title('Recorder - ' + filename)

    def set_modified(self, modified):
        self.modified = modified
        # Ghost some of the menues depending on state

    def open_window(self):
        self.tk = tk = Tk()  # segfault here

        self.set_filename(self.filename)

        menubar = Frame(tk, borderwidth=2, relief=RAISED)
        menubar.pack(side=TOP, fill=X)

        menu = Menubutton(menubar, text='File', underline=0)
        menu.pack(side=LEFT, padx="1m")
        menu.menu = Menu(menu)
        menu.menu.add_command(label='New', underline=0, 
                                command=self.new)
        menu.menu.add_command(label='Load...', underline=0, 
                                command=self.load)
        menu.menu.add_command(label='Save', underline=0, 
                                command=self.save)
        menu.menu.add_command(label='Save As...', underline=0, 
                                command=self.saveas)
        menu.menu.add_command(label='Quit', underline=0, 
                                command=self.quit)
        menu['menu'] = menu.menu
        #self.file_menu = menu


        menu = Menubutton(menubar, text='Help', underline=0)
        menu.pack(side=LEFT, padx="1m")
        menu.menu = Menu(menu)
        menu.menu.add_command(label='About...', underline=0, 
                                command=self.about)
        menu['menu'] = menu.menu
        #self.file_menu = menu


        display = Frame(tk)
        display.pack()

        f = Frame(display)
        f.pack(side=RIGHT)

        self.layer_display = LayerDisplay(f, width=config.layer_display_width,
                                          layer_height=20, bufsize=self.bufsize)
        self.layer_display.pack(side=TOP)

        if config.show_segment_display:
            self.segment_display = SegmentDisplay(f, width=config.layer_display_width,
                                                  layer_height=20, bufsize=self.bufsize)
            self.segment_display.pack(side=TOP)

        if config.show_peak_meters:
            h = self.layer_display.height
            self.output_peak_meter = PeakMeter(display, 14, h)
            self.output_peak_meter.pack(side=RIGHT)
            #self.input_peak_meter = PeakMeter(display, 14, h)
            #self.input_peak_meter.pack(side=RIGHT)
 

        controls = Frame(tk)
        controls.pack(side=TOP)
        
        if config.show_half_speed_control:
            half_speed = Toggle(controls, 'Half speed', _record.set_half_speed)
            half_speed.pack(side=LEFT)
        if config.show_monitor_input_control:
            monitor_input = Toggle(controls, 'Monitor input', _record.set_monitor_input)
            monitor_input.pack(side=LEFT)

        # Top layer controls
        frame = Frame(controls)
        frame.pack(side=LEFT)
        if config.show_undo_button:
            self.undo_button = Button(frame, text='Undo', command=self.undo)
            self.undo_button.pack(side=LEFT)
        if config.show_top_level_control:
            self.top_level = LevelControl(frame, _record.set_top_level)
            self.top_level.pack(side=LEFT)

        # Position display
        if config.show_status_display:
            self.status_display = Label(controls)
            self.status_display.pack(side=LEFT)

        # Transport controls
        frame = Frame(controls)
        frame.pack(side=LEFT) 
        Button(frame, text='Rec', bg='red', fg='white', command=self.record).pack(side=LEFT)
        Button(frame, text='Stop', command=self.stop).pack(side=LEFT)
        Button(frame, text='Play', command=self.play).pack(side=LEFT)

        self.mode = STOPPED
        self.switch_mode(STOPPED)  # Make sure the controls are in the correct state

        tk.bind('<KeyPress-q>', lambda x: self.quit())
        tk.bind('<KeyPress-b>', lambda x: self.record())
        tk.bind('<KeyPress-n>', lambda x: self.play())
        tk.bind('<KeyPress-space>', lambda x: self.stop())
        if config.show_undo_button:
            tk.bind('<KeyPress-BackSpace>', lambda x: self.undo())
        if config.show_half_speed_control:
            tk.bind('<KeyPress-h>', lambda x: half_speed.toggle())
        if config.show_monitor_input_control:
            tk.bind('<KeyPress-m>', lambda x: monitor_input.toggle())
        if config.show_top_level_control:
            tk.bind('<KeyPress-z>', lambda x: self.top_level.adjust(-0.1))
            tk.bind('<KeyPress-x>', lambda x: self.top_level.adjust(0.1))

        # Debugging
        def print_segment_list(*args):
            import pprint
            pprint.pprint(_record.get_segments())
        tk.bind('<KeyPress-s>', print_segment_list)
        
        status = _record.get_status()
        if status['used_end'] > 0:
            self.layer_display.reset(status['used_start'], status['used_end'])

    def update_display(self):
        status = _record.get_status()

        if config.show_status_display:
            if config.complex_status_display:
                pos = format_pos(status['pos'])
                used = format_pos(status['used_end'])
                total = format_pos(status['total_end'])
                
                self.status_display['text'] = 'pos: %s - used: %s - total: %s' % (pos, used, total)
            else:
                pos = format_pos(status['pos'])
                self.status_display['text'] = pos

        self.layer_display.update(status['pos'],
                                  status.get('top_start', 0),
                                  status.get('top_end', 0))

        if config.show_peak_meters:
            #self.input_peak_meter.update(status['input_peak'])
            self.output_peak_meter.update(status['output_peak'])

        if config.show_segment_display:
            segments = _record.get_segments()
            self.segment_display.update(status['pos'], segments)

        self.tk.after(100, self.update_display)

    def run(self):
        err = _record.audio_start()
        if err:
            tkMessageBox.showerror('Record',
                                  'Could not open sound device:\n'+err)
        else:
            self.update_display()
            self.tk.mainloop()
            _record.audio_stop()

    def __end__(self):
        _record.cleanup()

    def switch_mode(self, new_mode):
        if config.show_undo_button:
            if self.top_layer_exists:
                self.undo_button['state'] = 'active'
            else:
                self.undo_button['state'] = 'disabled'

        _record.switch_mode(new_mode)
        self.mode = new_mode

    def record(self):
        self.top_layer_exists = 1
        self.set_modified(1)
        self.layer_display.new_layer()
        self.switch_mode(RECORDING)
        if config.show_top_level_control:
            self.top_level.reset()

    def play(self):
        self.switch_mode(PLAYING)

    def stop(self):
        self.switch_mode(STOPPED)

    def undo(self):
        self.top_layer_exists = 0
        self.layer_display.discard_layer()
        _record.undo()
        self.switch_mode(STOPPED)
        self.top_level.reset()


    def ok_to_clear(self):
        if self.modified:
            filename = self.filename or 'Untitled'
            if tkMessageBox.askokcancel('Record: %s modified' % filename,
                'Changes made to %s.\nGo ahead anyway?' % filename):
                self.set_modified(0)
                return 1
            else:
                return 0
        else:
            return 1

    def new(self):
        self.switch_mode(STOPPED)
        if self.ok_to_clear():
            self.set_modified(0)
            self.set_filename(None)
            self.layer_display.clear()
            _record.clear()
            pass

    def load(self):
        self.switch_mode(STOPPED)
        if self.ok_to_clear():
            filename = tkFileDialog.askopenfilename()
            self.load_recording(filename)

    def save(self):
        self.switch_mode(STOPPED)
        if self.filename:
            self.save_recording(filename)
        else:
            self.saveas()

    def saveas(self):
        self.switch_mode(STOPPED)
        filename = tkFileDialog.asksaveasfilename()
        if filename:
            self.save_recording(filename)

    def quit(self):
        self.switch_mode(STOPPED)
        if self.ok_to_clear():
            self.tk.quit()

    def about(self):
        tkMessageBox.showinfo('About Record',
'''Record
(I should come up with a better name)

by Ole Martin Bjorndalen
olemb@stud.cs.uit.no
http://www.cs.uit.no/~olemb/''')

    def load_recording(self, filename):
        self.top_layer_exists = 0
        self.set_modified(0)
        _record.audio_pause()
        #self.tk.config(cursor='wait')
        _record.load_recording(filename)
        #self.tk.config(cursor='')
        _record.audio_resume()
        self.set_filename(filename)

        status = _record.get_status()
        self.layer_display.reset(status['used_start'], status['used_end'])

    def save_recording(self, filename):
        self.set_modified(0)
        _record.audio_pause()
        #self.tk.config(cursor='wait')
        _record.save_recording(filename)
        #self.tk.config(cursor='')
        _record.audio_resume()
        self.set_filename(filename)

secs = 70
recorder = Recorder(secs)
if sys.argv[1:]:
    filename = sys.argv[1]
    recorder.tk.after(10, lambda: recorder.load_recording(filename))

recorder.run()
