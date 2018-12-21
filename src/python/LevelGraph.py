import Tkinter

import audioop

class LevelGraph(Tkinter.Frame):
    def __init__(self, root, params, width, height):
        Tkinter.Frame.__init__(self, root, borderwidth=2, relief='sunken')

        baselinecolor = 'white'
        self.linecolor = 'blue'
        self.bgcolor = 'gray85'

        self.params = params
        
        self.width = width
        self.height = height
        self.canvas = Tkinter.Canvas(self, width=width, height=height, background=self.bgcolor)
        self.canvas.pack()
        self.lines = []
        self.pos = 0
        self.middle = self.height / 2
        self.headroom = self.middle

        self.baseline = self.canvas.create_line(0, self.middle, self.width, self.middle, fill=baselinecolor)

        for x in range(self.width):
            l = self.canvas.create_line(x, self.middle, x, self.middle, fill=self.linecolor, tag='line')
            self.lines.append(l)

        self.buffered_blocks = []

    def invert(self):
        self.linecolor, self.bgcolor = self.bgcolor, self.linecolor
        self.canvas['background'] = self.bgcolor
        self.canvas.itemconfigure('line', fill=self.linecolor)

    def feed(self, *blocks):
        mix = blocks[0]
        remaining = list(blocks[1:])
        while remaining:
            mix = audioop.add(mix, remaining.pop(), self.params.sampwidth)
        self.buffered_blocks.append(mix)

        if len(self.buffered_blocks) == 4:
            block = ''.join(self.buffered_blocks)
            self.buffered_blocks = []
            
            minval, maxval = audioop.minmax(block, self.params.sampwidth)

            minval = minval * self.headroom / self.params.scale
            maxval = maxval * self.headroom / self.params.scale
            
            self.canvas.coords(self.lines[self.pos], self.pos, self.middle-minval, self.pos, self.middle-maxval)
            
            self.pos = (self.pos + 1) % self.width

    def test_feed(self, *blocks):
        mix = blocks[0]
        remaining = list(blocks[1:])
        while remaining:
            mix = audioop.add(mix, remaining.pop(), self.params.sampwidth)
        self.buffered_blocks.append(mix)

        if len(self.buffered_blocks) == 4:
            block = ''.join(self.buffered_blocks)
            self.buffered_blocks = []
            
            maxval = audioop.max(block, self.params.sampwidth)

            maxval = maxval * self.height / self.params.scale
            
            self.canvas.coords(self.lines[self.pos], self.pos, self.height-maxval, self.pos, self.height)
            
            self.pos = (self.pos + 1) % self.width
