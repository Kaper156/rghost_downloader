from threading import Thread
from tkinter import *
from tkinter.ttk import *
import rghost_back as rghost

class Wrapper(Tk):
    def __init__(self, **kwargs):
        Tk.__init__(self, **kwargs)

        self.geometry('400x600+300+300')
        self.title('rghost.ru search and download')

        self.result = set()
        self.query = StringVar()
        self.ext = StringVar()
        self.parser = None
        self.downer = None

        # Search bar
        search_bar = Frame(self)

        s_f = Frame(search_bar)
        Label(s_f, text='Search:').pack(side=LEFT)
        Entry(s_f, textvariable=self.query, width=42).pack(side=RIGHT)
        s_f.pack(side=TOP, fill=X)

        s_e = Frame(search_bar)
        Label(s_e, text='Extension:').pack(side=LEFT)
        Entry(s_e, textvariable=self.ext, width=7).pack(side=LEFT)
        Button(s_e, text='Parse!', command=self.parse).pack(side=LEFT)
        self.bt_down = Button(s_e, text='Down to...', command=self.download)
        self.bt_down['state'] = "disabled"
        self.bt_down.pack(side=RIGHT)
        s_e.pack(side=TOP, fill=X)

        search_bar.pack(side=TOP)

        # TableContent
        content_frame = LabelFrame(self, text='Founded:')

        self.content_view = Treeview(content_frame, columns=('url', 'size'), height=24)

        self.content_view.heading('#0', text='Title')
        self.content_view.column('#0', width=140)

        self.content_view.heading('url', text='URL')
        self.content_view.column('url', width=185)

        self.content_view.heading('size', text='Size')
        self.content_view.column('size', width=70)

        # Right-click = delete item
        def del_content(evt):
            for item in self.content_view.selection():
                self.content_view.delete(item)
        self.content_view.bind('<Button-3>', del_content)

        self.content_view.pack(side=LEFT)

        content_frame.pack(side=TOP)
        self.status = StringVar()
        Label(self, textvariable=self.status).pack(side=TOP)
        self.progressbar = Progressbar(self, orient=HORIZONTAL, length=400)
        self.progressbar.pack(side=BOTTOM)

        mainloop()

    def update_content_view(self, files):
        self.content_view.delete(*self.content_view.get_children())
        # while files.qsize() > 0:
        #     self.result.update([files.get()])
        # for file in list(self.result):
        #     self.content_view.insert('', END, text=file.title, values=(file.url, file.size))
        self.result = []
        while files.qsize() > 0:
            file = files.get()
            self.result.append(file)
            self.content_view.insert('', END, text=file.title, values=(file.url, file.size))

        if len(self.content_view.get_children()):
            self.bt_down['state'] = "normal"
        else:
            self.bt_down['state'] = "disabled"

    def parse(self):
        if not self.query.get().strip():
            return
        ext = self.ext.get()
        self.parser = rghost.Parser(self.query.get(), extension=ext)
        self.after_idle(self.update_content_view, self.parser.start())
        Thread(target=lambda: self.progress_download(40, self.parser.queue)).start()

    def download(self):
        from tkinter.filedialog import askdirectory
        destination = askdirectory(initialdir='.')
        if len(destination) < 1:
            return
        self.downer = rghost.LinkLoader(destination, files=list(self.result))
        self.downer.start()
        Thread(target=lambda: self.progress_download(len(self.result), self.downer.que)).start()

    def progress_download(self, total, queue):
        self.progressbar['variable'] = p_var = IntVar()
        while True:
            from time import sleep
            q = queue.qsize()
            if q < 1:
                p_var.set(0)
                self.status.set('Work Done!')
                break
            q = (total-q)
            a = q * 100 / total
            self.status.set('%s/%s' % (q, total))
            print('q =', q)
            print('a =', a)
            print()
            p_var.set(a)

            sleep(0.5)


a = Wrapper()
