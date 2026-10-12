"""Cached Fluent surfaces with native ttk input and keyboard behavior."""
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk

BG, SURFACE, TEXT, MUTED = '#F5F5F5', '#FFFFFF', '#242424', '#616161'
ACCENT, HOVER, PRESSED, ACCENT_TEXT = '#72B6E8', '#62A9DC', '#529ACD', '#102C40'
BORDER, CARD_BORDER = '#D1D1D1', '#E5E5E5'


class FluentTheme:
    def __init__(self, root, scale):
        self.root, self.scale = root, scale
        self.images = []
        self.prefix = f'Fishing{round(scale*96)}'
        self.style = ttk.Style(root)
        self.style.theme_use('clam')
        self.install()
        names=('Card.TFrame','Primary.TButton','Secondary.TButton','Help.TButton','TEntry','TCombobox',
               'TCheckbutton','TRadiobutton','Vertical.TScrollbar')
        self.layouts={name:self.style.layout(name) for name in names}
        self.configs={name:self.style.configure(name) for name in names}

    def px(self, value):
        return max(1, round(value*self.scale))

    def image(self, size, painter):
        size = tuple(self.px(n) for n in size)
        canvas = Image.new('RGBA', tuple(n*4 for n in size))
        painter(ImageDraw.Draw(canvas), canvas.size, self.scale*4)
        photo = ImageTk.PhotoImage(canvas.resize(size, Image.Resampling.LANCZOS), master=self.root)
        self.images.append(photo)
        return photo

    def panel(self, fill, outline, radius, backdrop, large=False):
        def draw(pen, size, unit):
            pen.rectangle((0, 0, *size), fill=backdrop)
            edge = max(1, round(unit))
            pen.rounded_rectangle((edge/2, edge/2, size[0]-edge/2, size[1]-edge/2),
                                  radius=round(radius*unit), fill=fill, outline=outline, width=edge)
        return self.image((480, 320) if large else (320, 48), draw)

    def element(self, name, normal, states=(), radius=6):
        name = self.prefix+'.'+name
        if name not in self.style.element_names():
            self.style.element_create(name, 'image', normal, *states, border=self.px(radius+2),
                                      padding=self.px(1), sticky='nswe',
                                      width=self.px(radius*2+5), height=self.px(radius*2+5))
        return name

    def install(self):
        s = self.style
        s.configure('.', font='TkDefaultFont', background=BG, foreground=TEXT)
        s.configure('TFrame', background=BG)
        s.configure('TLabel', background=BG, foreground=TEXT)
        s.configure('Title.TLabel', font='FishingTitleFont')
        s.configure('Muted.TLabel', foreground=MUTED)
        s.configure('Card.TLabel', background=SURFACE)
        s.configure('CardMuted.TLabel', background=SURFACE, foreground=MUTED)
        s.configure('Count.TLabel', background=SURFACE, font='FishingCountFont')
        card = self.element('card', self.panel(SURFACE, CARD_BORDER, 8, BG, True), radius=8)
        s.layout('Card.TFrame', [(card, {'sticky':'nswe'})])
        s.configure('Card.TFrame', background=SURFACE)
        s.configure('Surface.TFrame', background=SURFACE)
        self.button('Primary', ACCENT, HOVER, PRESSED, ACCENT_TEXT)
        self.button('Secondary', SURFACE, '#F5F5F5', '#EBEBEB', TEXT, BORDER)
        self.button('Help', BG, '#EBEBEB', '#E0E0E0', MUTED)
        s.configure('Help.TButton', padding=self.px(3))
        self.play_icons = {k:self.symbol('play', c) for k,c in [('normal', ACCENT_TEXT), ('disabled','#A0A0A0')]}
        self.stop_icons = {k:self.symbol('stop', c) for k,c in [('normal', TEXT), ('disabled','#A0A0A0')]}
        self.help_icon = self.symbol('help', MUTED)
        self.fields()
        self.checkbox()
        self.radio()
        s.configure('Vertical.TScrollbar', background='#D6D6D6', troughcolor=SURFACE,
                    borderwidth=0, width=self.px(6), arrowsize=0)
        s.map('Vertical.TScrollbar', background=[('pressed','#999999'), ('active','#ADADAD')])
        s.layout('Vertical.TScrollbar', [('Vertical.Scrollbar.trough', {'sticky':'ns', 'children':[
            ('Vertical.Scrollbar.thumb', {'expand':True, 'sticky':'nswe'})]})])

    def button(self, name, normal, hover, pressed, color, border=None):
        normal_image = self.panel(normal, border or normal, 6, BG)
        states = [('disabled', self.panel('#F0F0F0', '#E5E5E5', 6, BG)),
                  ('pressed', self.panel(pressed, border or pressed, 6, BG)),
                  ('active', self.panel(hover, border or hover, 6, BG)),
                  ('focus', self.panel(normal, ACCENT_TEXT if name=='Primary' else ACCENT, 6, BG))]
        element = self.element(name, normal_image, states)
        self.style.layout(name+'.TButton', [(element, {'sticky':'nswe', 'children':[
            ('Button.padding', {'sticky':'nswe', 'children':[('Button.label', {'sticky':'nswe'})]})]})])
        self.style.configure(name+'.TButton', font='TkDefaultFont', foreground=color,
                             padding=(self.px(12),self.px(10)), borderwidth=0, anchor='center')
        self.style.map(name+'.TButton', foreground=[('disabled','#A0A0A0')])

    def symbol(self, kind, color):
        def draw(pen, size, unit):
            w,h = size
            if kind=='play':
                pen.polygon([(w*.27,h*.17),(w*.8,h*.5),(w*.27,h*.83)], fill=color)
            elif kind=='stop':
                pen.rounded_rectangle((w*.23,h*.23,w*.77,h*.77), radius=unit, fill=color)
            else:
                pen.ellipse((unit,unit,w-unit,h-unit), outline=color, width=max(1,round(unit)))
                face=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', round(h*.72))
                pen.text((w*.5,h*.49), '?', font=face, fill=color, anchor='mm')
        return self.image((16,16),draw)

    def fields(self):
        normal = self.panel(SURFACE, BORDER, 4, SURFACE)
        focus = self.panel(SURFACE, ACCENT, 4, SURFACE)
        disabled = self.panel('#F0F0F0', CARD_BORDER, 4, SURFACE)
        border = self.element('field', normal, [('disabled',disabled), ('focus',focus)], radius=4)
        s = self.style
        s.layout('TEntry', [(border, {'sticky':'nswe', 'children':[
            ('Entry.padding', {'sticky':'nswe','children':[('Entry.textarea', {'sticky':'nswe'})]})]})])
        s.configure('TEntry', padding=(self.px(8),self.px(5)), borderwidth=0,
                    fieldbackground=SURFACE, foreground=TEXT, selectbackground=ACCENT, selectforeground=ACCENT_TEXT)
        s.map('TEntry', foreground=[('disabled','#A0A0A0')],
              fieldbackground=[('disabled','#F0F0F0'), ('readonly',SURFACE)])
        def arrow(pen,size,unit):
            w,h=size
            pen.line([(w*.3,h*.4),(w*.5,h*.6),(w*.7,h*.4)],fill=MUTED,width=max(1,round(unit)))
        arrow_image=self.image((28,20),arrow)
        arrow_name=self.prefix+'.arrow'
        if arrow_name not in s.element_names():
            s.element_create(arrow_name,'image',arrow_image,sticky='')
        s.layout('TCombobox',[(border, {'sticky':'nswe','children':[
            (arrow_name, {'side':'right','sticky':'ns'}),
            ('Combobox.padding', {'sticky':'nswe','children':[('Combobox.textarea',{'sticky':'nswe'})]})]})])
        s.configure('TCombobox',padding=(self.px(8),self.px(5)),borderwidth=0,foreground=TEXT,
                    fieldbackground=SURFACE,selectbackground=SURFACE,selectforeground=TEXT)
        s.map('TCombobox',foreground=[('disabled','#A0A0A0'),('readonly',TEXT)],
              fieldbackground=[('disabled','#F0F0F0'),('readonly',SURFACE)],
              selectbackground=[('readonly',SURFACE)],selectforeground=[('readonly',TEXT)])
        self.root.option_add('*TCombobox*Listbox.font', 'TkDefaultFont')
        self.root.option_add('*TCombobox*Listbox.background', SURFACE)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', ACCENT_TEXT)

    def checkbox(self):
        def indicator(selected, disabled=False):
            def draw(pen,size,unit):
                w,h=size
                fill='#E5E5E5' if disabled else ACCENT if selected else SURFACE
                outline=CARD_BORDER if disabled else ACCENT if selected else BORDER
                pen.rounded_rectangle((unit,unit,w-unit,h-unit),radius=unit*3,fill=fill,
                                      outline=outline,width=max(1,round(unit)))
                if selected:
                    pen.line([(w*.25,h*.5),(w*.43,h*.68),(w*.76,h*.32)],
                             fill='#A0A0A0' if disabled else ACCENT_TEXT,width=max(1,round(unit*1.5)))
            return self.image((18,18),draw)
        off,on,disabled,disabled_on=(indicator(False),indicator(True),indicator(False,True),indicator(True,True))
        name=self.prefix+'.check'
        if name not in self.style.element_names():
            self.style.element_create(name,'image',off,('disabled','selected',disabled_on),
                                      ('disabled',disabled),('selected',on),sticky='')
        self.style.layout('TCheckbutton',[('Checkbutton.padding',{'sticky':'nswe','children':[
            (name,{'side':'left','sticky':''}),
            ('Checkbutton.focus',{'side':'left','sticky':'nswe','children':[
                ('Checkbutton.label',{'sticky':'nswe'})]})]})])
        self.style.configure('TCheckbutton',background=BG,indicatormargin=(0,0,self.px(6),0),padding=0)
        self.style.map('TCheckbutton',foreground=[('disabled','#A0A0A0')],background=[('active',BG)])

    def activate(self):
        """Select cached elements after a DPI change; never rerasterize on resize."""
        self.install_layouts()

    def radio(self):
        def indicator(selected,disabled=False):
            def draw(pen,size,unit):
                _,h=size
                w=h
                outline='#BDBDBD' if disabled else ACCENT if selected else '#8A8A8A'
                pen.ellipse((unit,unit,w-unit,h-unit),fill=SURFACE,outline=outline,
                            width=max(1,round(unit*(2 if selected else 1))))
                if selected:
                    pen.ellipse((w*.32,h*.32,w*.68,h*.68),fill=outline)
            return self.image((20,18),draw)
        off,on,disabled,disabled_on=indicator(False),indicator(True),indicator(False,True),indicator(True,True)
        name=self.prefix+'.radio'
        if name not in self.style.element_names():
            self.style.element_create(name,'image',off,('disabled','selected',disabled_on),
                                      ('disabled',disabled),('selected',on),sticky='')
        self.style.layout('TRadiobutton',[('Radiobutton.padding',{'sticky':'nswe','children':[
            (name,{'side':'left','sticky':''}),
            ('Radiobutton.focus',{'side':'left','sticky':'nswe','children':[
                ('Radiobutton.label',{'sticky':'nswe'})]})]})])
        self.style.configure('TRadiobutton',background=SURFACE,indicatormargin=(0,0,self.px(6),0),padding=0)
        self.style.map('TRadiobutton',foreground=[('disabled','#A0A0A0')],background=[('active',SURFACE)])

    def install_layouts(self):
        # Cached instances hold their image elements. Reuse the saved layouts
        # rather than creating images or elements again when revisiting a DPI.
        for name,layout in self.layouts.items():
            self.style.layout(name,layout)
            self.style.configure(name,**self.configs[name])
