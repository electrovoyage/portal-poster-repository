from ttkbootstrap import *
from ttkbootstrap.scrolled import ScrolledText, ScrolledFrame
from PIL import Image, ImageTk
import requests
from io import BytesIO
import sys
from tkinter import Event
from electrovoyage_asset_unpacker import AssetPack
import json

win = Window('Aperture Science Definitive Poster & Signage Database', 'yeti', size=(1000, 700))
#win.withdraw()

posterpane = Panedwindow(win, orient=HORIZONTAL, style=SECONDARY)
posterpane.pack(expand=True, fill=BOTH)

posterlistframe = Frame(win)
posterpane.add(posterlistframe, weight=1)

search_bar = Entry(posterlistframe)
search_bar.pack(side=TOP, anchor=N, fill=X, padx=5, pady=5)#, fill=X, expand=True)
#search_bar.pack(side=TOP, fill=X, expand=True, anchor=N)

posterlist = ScrolledFrame(posterlistframe, padding=10)
posterlist.pack(side=TOP, fill=BOTH, expand=True, anchor=N)

selectedposter = Frame(win, padding=5)
posterpane.add(selectedposter, weight=0)

selposter_preview = Label(selectedposter, compound=TOP)
selposter_preview.pack(side=TOP, expand=True)

selposter_contents = Text(selectedposter, state=DISABLED)
selposter_contents.pack(side=TOP, fill=X)

IMAGE_URL_PREFIX = 'https://electrovoyage.github.io/cdn/posters/'
IMAGE_PATH_PREFIX = 'resources/'

if '--pack' not in sys.argv:
    pack_resp = requests.get(IMAGE_URL_PREFIX + 'assets.packed')
    pack_dat = pack_resp.content
    if pack_resp.status_code != 200:
        raise Exception(f'failed to retrieve asset package, return code: {pack_resp.status_code}')
else:
    i = sys.argv.index('--pack')
    file = sys.argv[i + 1]
    
    with open(file, 'rb') as _pack_file:
        pack_dat = _pack_file.read()

pack_f = BytesIO(pack_dat)
pack = AssetPack(pack_f, emulated=True)

_posterinfo = json.load(pack.getfile('resources/posters.json'))

class PosterInfo:
    def __init__(self, dat: dict):
        self.material: str = dat['material']
        self.contents: str = dat['contents']
        
        self.frames: list[Image.Image] = []
        self.framestk: list[ImageTk.PhotoImage] = []
        self.lgframes: list[Image.Image] = []
        self.lgframestk: list[ImageTk.PhotoImage] = []
        
        if dat['image'].split('.')[1] == 'png':
            self.imagepath: str = IMAGE_PATH_PREFIX + dat['image']
            self.image_f = pack.getfile(self.imagepath)
            self.image = Image.open(self.image_f)
            
            w, h = self.image.size
            
            aspect_ratio = w / h
            height = 128
            width = round(height * aspect_ratio)
            
            self.small_image = self.image.resize((width, height), Image.BICUBIC)
            
            height = 256
            width = round(height * aspect_ratio)
            
            self.image = self.image.resize((width, height), Image.BICUBIC)
            
            self.smallimagetk = ImageTk.PhotoImage(self.small_image)
            self.imagetk = ImageTk.PhotoImage(self.image)
            self.animated = False
            
        elif dat['image'].split('.')[1] == 'json':
            anim_data = json.load(pack.getfile(IMAGE_PATH_PREFIX + dat['image']))
            
            for i in range(1, anim_data['frames'] + 1):
                img = Image.open(pack.getfile(f'{IMAGE_PATH_PREFIX}{anim_data['folder']}/{i}.png'))
                w, h = img.size

                aspect_ratio = w / h

                height = 256
                width = round(height * aspect_ratio)

                img = img.resize((width, height), Image.BICUBIC)
                
                self.frames.append(img)
                if i == 1:
                    self.image = img
                    self.imagetk = ImageTk.PhotoImage(self.image)
                    
                    height = 128
                    width = round(height * aspect_ratio)

                    small_img = img.resize((width, height), Image.BICUBIC)
                    
                    self.small_image = small_img
                    self.smallimagetk = ImageTk.PhotoImage(self.small_image)
                    
                self.framestk.append(ImageTk.PhotoImage(img))
                
            self.animated = True
            self.framenum = IntVar(value=-1)
        
        self.style: str = dat['style']
        self.sources: list[str] = dat['sources']
            
    def setframe(self, fr: Frame):
        self.frame = fr
        
    def __repr__(self) -> str:
        return f'<PosterInfo with contents={repr(self.contents)}>'
    
    __str__ = __repr__
        
    def select(self):
        global selectedposterinfo
        if selectedposterinfo != None:
            if selectedposterinfo.animated:
                selposter_preview.after_cancel(selectedposterinfo.nextframe)
                selectedposterinfo.framenum.set(0)
        
        if not self.animated:
            selposter_preview.configure(image=self.imagetk)
        else:
            selposter_preview.configure(image=self.framestk[0])
            self.nextframe = selposter_preview.after(500, self.increaseframe)
        
        selectedposterinfo = self
        selposter_contents.configure(state=NORMAL)
        selposter_contents.delete('0.0', END)
        selposter_contents.insert(END, self.contents)
        selposter_contents.configure(state=DISABLED)
            
    def increaseframe(self):
        fcount = len(self.frames)
        
        newframe = self.framenum.get() + 1
        if newframe >= fcount:
            newframe = 0
        
        self.framenum.set(newframe)
        newframeimg = self.framestk[newframe]
        
        selposter_preview.configure(image=newframeimg)
        
        self.nextframe = selposter_preview.after(500, self.increaseframe)
   
global selectedposterinfo
selectedposterinfo: PosterInfo = None
        
posterinfo = [PosterInfo(i) for i in _posterinfo]
posterframes: list[Frame] = []

POSTER_PACK_PARAMS = {'side': TOP, 'fill': X, 'anchor': N, 'expand': True}

for i in posterinfo:
    fr = Frame(posterlist, padding=10)
    
    def onclick(x: Event):
        obj: Frame | Label = x.widget
        if isinstance(obj, Label):
            fr = obj.master
        else:
            fr = obj
        fr.configure(relief=SUNKEN)
        
    def onrelease(x: Event):
        obj: Frame | Label = x.widget
        if isinstance(obj, Label):
            fr = obj.master
        else:
            fr = obj
        fr.configure(relief=FLAT)
        
        i = posterinfo[posterframes.index(fr)]
        i.select()
        
    fr.bind('<Button-1>', onclick)
    fr.bind('<ButtonRelease-1>', onrelease)
    label1 = Label(fr, text=i.material)
    label1.pack(side=LEFT, fill=X, expand=True)
    
    label2 = Label(fr, compound=RIGHT, image=i.smallimagetk)
    label2.pack(side=RIGHT, expand=True, anchor=E)
    
    label1.bind('<Button-1>', onclick)
    label1.bind('<ButtonRelease-1>', onrelease)
    
    label2.bind('<Button-1>', onclick)
    
    label2.bind('<ButtonRelease-1>', onrelease)
    fr.pack(**POSTER_PACK_PARAMS)
    
    i.setframe(fr)
    posterframes.append(fr)
    
def search():
    kwds = search_bar.get().split(' ')
    
    for poster in posterinfo:
        poster.sorting_value = 0
        poster.frame.pack_forget()
        for word in kwds:
            poster.sorting_value += poster.contents.lower().count(word.lower())
            
    sorted_list = posterinfo.copy()
    sorted_list: list[PosterInfo] = list(filter(lambda x: x.sorting_value > 0, sorted_list))
    sorted_list.sort(key=lambda x: x.sorting_value, reverse=True)

    for poster in sorted_list:
        poster.frame.pack(**POSTER_PACK_PARAMS)
    
search_bar.bind('<Return>', lambda x: search())

win.mainloop()