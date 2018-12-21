import Tkinter
import audioop

class Layer:
    def __init__(self, start=0, end=0):
        self.start = start
        self.end = end
        self.rect = None

class LayerDisplay:
    def __init__(self, parent, recorder, width=400, height=100):
        self.rec = recorder
        self.layer_height = 20
        self.layer_dist = 5  # Distance between layers

        self.width = width
        self.height = height
        self.maxlayers = 16
        self.cursor_height = self.layer_height / 2
        
        self.canvas = Tkinter.Canvas(parent, width=width, height=self.height, bd=2, relief='sunken')

        self.top = None
        self.layers = []

        self.size = 0
        self._resize()  # sets self.size and self.scale

        self.cursor = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill='black', outline='')
        self.prev_pos = -1  # Force a redraw

        self.add_bindings()

    def pack(self, *args, **kw):
        self.canvas.pack(*args, **kw)

    def add_bindings(self):
        
        def play_motion(event):
            pos = max(0, int(event.x / self.scale))
            self.rec.play(pos)

        def click_play(event):
            self.canvas.bind('<Motion>', play_motion)
            self.canvas.bind('<ButtonRelease-1>', play_release)
            play_motion(event)

        def play_release(event):
            self.canvas.unbind('<Motion>')
            self.canvas.unbind('<ButtonRelease-1>')

        def click_record(event):
            pos = max(0, int(event.x / self.scale))
            self.rec.record(pos)
            self.record()

        self.canvas.bind('<ButtonPress-1>', click_play)
        self.canvas.bind('<ButtonPress-3>', click_record)

    def _resize(self):
        "Resize the display to fit the recording"

        oldsize = self.size

        recend = max([layer.end for layer in self.layers]+[0])

        self.size = int(self.rec.params.secs2pos(10))  # Minimum size

        while self.size < recend:
            self.size *= 2
        self.scale = float(self.width) / float(self.size)

        # Redraw layers if size changed
        if self.size != oldsize:
            for layer in self.layers:
                self._redraw_layer(layer)

    def _redraw_layer(self, layer):
        # Grow the recording
        c = self.canvas.coords(layer.rect)
        c = (layer.start * self.scale, c[1], layer.end * self.scale, c[3])
        self.canvas.coords(layer.rect, c)

    def _redraw_cursor(self, pos):
        x = pos * self.scale
        h = self.cursor_height
        self.canvas.coords(self.cursor, x-h/2, 0, x, h, x+h/2, 0)
        self.canvas.tkraise(self.cursor)

    def update(self):
        # Todo: check if cursor is beyond the end of the display

        pos = self.rec.pos
        mode = self.rec.mode

        if mode == 'recording':
            self.top.end += 1

            if self.top.end > self.size:
                self._resize()

        screen_pos = int((pos * self.scale))
        screen_prev_pos = int((self.prev_pos * self.scale))

        # Only redraw if we have to
        if screen_pos != screen_prev_pos:
            self._redraw_cursor(pos)
            if self.top and mode == 'recording':
                self._redraw_layer(self.top)

        self.prev_pos = pos

    def clear(self):
        "Clear all layers in the display"
        self.top = None
        self.canvas.delete('layers')
        self.layers = []
        self._resize()

    def record(self):
        "Start a new recording"

        pos = self.rec.pos

        if self.top:
            self.canvas.itemconfigure(self.top.rect, fill='white')

        self.top = self._add_layer(pos, pos, fill='blue')

    def undo(self):
        if self.top != None:
            self.canvas.delete(self.top.rect)
            
            self.canvas.move('layers', 0, -self.layer_dist)

            self.layers.pop()
            self.top = None

            self._resize()

    def _add_layer(self, start, end, fill='blue'):
        self.canvas.move('layers', 0, self.layer_dist)

        y = self.cursor_height  # Leave room for the cursor
        
        layer = Layer(start, end)
        layer.rect = self.canvas.create_rectangle(
            layer.start * self.scale, y,
            layer.end * self.scale, y + self.layer_height,
            fill=fill,
            tag='layers')
        self.layers.append(layer)

        return layer
            
    def file_loaded(self):
        self.clear()
        self._add_layer(0, len(self.rec), fill='white')
        self._resize()
