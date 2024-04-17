from lib import YouTube
import os
from time import clock
import urllib
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import base64
from tkinter import *
from tkinter import Tk ,StringVar, ttk
from tkinter import filedialog
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import threading
import time
import queue as queue
import math
import re
from Icon import iconmap
import socket 

socket.setdefaulttimeout(600)
root = Tk()
quality = StringVar()
progress  = 0
file_size = 1
bytes_received = 0
taskStatus = 0 
queue = queue.Queue()
outtime = 600
path = os.getcwd()

'''proxy_support = urllib.request.ProxyHandler({"http":"http://122.172.30.60:80"})
opener = urllib.request.build_opener(proxy_support)
urllib.request.install_opener(opener)'''




def setwidgetlayout():
    global quality
    # get screen width and height
    ws = root.winfo_screenwidth();  #This value is the width of the screen
    hs = root.winfo_screenheight(); #This is the height of the screen
    #Set screen dimentions
    w = 450;# 570; # width
    h = 260;# 400; # height
    # calculate position x, y
    x = (ws/2) - (w/2);
    y = (hs/2) - (h/2);
    
    
    root.geometry('%dx%d+%d+%d' % (w, h, x, y));

    # disable resize else it will spoil the layout.
    root.resizable(0,0); # only minimize or close allowed    
    videoFormat.place(x=5 , y=20)
    box['values'] = ('720p', '480p' , '360p')
    box.set('720p')
    box.place(x = 150, y=21)
    
    link.place(x=5,y=75)
    Save.place(x=410,y= 73)
  
    startDownload.place(x=140 , y=110)

    frame.place(x=5 , y =150 )
    progressBar.pack(side = LEFT)
    percantage.pack(side = RIGHT)
    ETR.place(x= 5 , y = 180)

    About.place(x=5,y=220)

    icondata= base64.b64decode(iconmap)
    tempFile = 'Icon.ico'
    iconfile = open(tempFile , 'wb')
    iconfile.write(icondata)
    iconfile.close()
    root.iconbitmap(tempFile)
    os.remove(tempFile)
    root.title("Youtube Downloader")
    #Exit.place (x=230,y=220)


class ThreadedClient(threading.Thread):

    def __init__(self ): 
        threading.Thread.__init__(self)

    def playlistvideo(self):
        finalurl = {}
        listofurl = []
        url = link.get()
        if 'http' not in url:
            url = 'http://' + url
        if 'list=' in url:
            eq = url.rfind('=') + 1
            piy = url[eq:]     # piy = playlist identity
        else :
            print('Incorrect Playlist \n')
        
        playlistcontent = urlopen(url , timeout = outtime)
        playlistcontent = playlistcontent.read()
        playlistcontent = str(playlistcontent)
            
        #patternstring = r'watch\?v=\S+?list=' + piy +  r'\S+'
        patternstring = r'watch\?v=\S+?index=\d+'
        pattern = re.compile(patternstring)
        overlappingpattern = re.findall(pattern, playlistcontent)
        
        if len(overlappingpattern) > 0:
            for i in overlappingpattern:
                urllinks = str(i)
                if 'index=' in urllinks:
                    index = urllinks.rfind("index=") + 6
                    key = int((re.findall(r'\d+' , urllinks[index:]))[0])
                    index = urllinks.index('&')
                    finalurl[key] = 'http://www.youtube.com/' + urllinks[:index]
            #Sorted(finalurl.items() gives you the list of tuples  
            listofurl = [value for key,value in sorted(finalurl.items())]
            
        if  len(listofurl) == 0 :            
            print('No Video found \n')
        else:
            return listofurl

    def videodownload(self ,urllink , msg):
        global queue
        global path
        chunk_size=8 * 1024
        on_finish=None
        force_overwrite=True
        
        yt = YouTube(urllink)
        
        files = yt.filter( resolution = box.get())
        if len(files) != 1 :
            video = max(yt.get_videos())
        else:
            video = files[0]
        filepath = os.path.normpath(path)
        if not os.path.isdir(filepath):
            raise OSError('Make sure path exists.')
        videoname = video.filename
        if '[Official Video]' in video.filename:
            videoname = video.filename.replace('[Official Video]' , '')

        filename = "{0}.{1}".format(videoname , video.extension)
        
        if len(videoname)>65 :
            index = videoname[:65].rfind(" ")
            videoname = "Downloading : " + videoname[:index]+ '\n' + videoname[index:]
        else:
            videoname = "Downloading : " + videoname
            

        queue.put(videoname)
        
        filepath = os.path.join(path, filename)
        
        # TODO: If it's not a path, this should raise an ``OSError``.
        # TODO: Move this into cli, this kind of logic probably shouldn't be
        # handled by the library.
        if os.path.isfile(filepath) and not force_overwrite:
            raise OSError("Conflicting filename:'{0}'".format(video.filename))
        # TODO: Split up the downloading and OS jazz into separate functions.
        initial = time.time()
        attempt = 0
        while attempt<20:
            try:
                response = urlopen(video.url , timeout = outtime)
                meta_data = dict(response.info().items())
                file_size = int(meta_data.get("Content-Length") or
                                meta_data.get("content-length"))
                break ;
            except Exception as e:
                print(str(e))
                attempt = attempt + 1
                continue
        if(os.path.isfile(filepath)) and os.path.getsize(filepath) == file_size:
            return
            
            
        bytes_received = 0
        
        


        # TODO: Let's get rid of this whole try/except block, let ``OSErrors``
        # fail loudly.
        
        try:
            with open(filepath, 'wb') as dst_file:
                while True:
                    video._buffer = response.read(chunk_size)
                    # Check if the buffer is empty (aka no bytes remaining).
                    if not video._buffer:
                        if on_finish:
                            # TODO: We possibly want to flush the
                            # `_bytes_recieved`` buffer before we call
                            # ``on_finish()``.
                            on_finish(filepath)
                        break

                    progress = len(video._buffer)            
                    bytes_received += progress
                    dst_file.write(video._buffer)
                    queue.put(str(int((bytes_received*100)/file_size)) + " %")
                    last = time.time()
                    speed = bytes_received/(last - initial)
                    tR = int((file_size-bytes_received)/speed)
                    queue.put( "Time Remaining : %d s    Speed : %sps   Size : %s    Remaining : %s"  %(tR ,sizeofspeed(speed) , sizeof(file_size) ,msg))
                    queue.put((100*progress)/file_size)                  
                    
        except KeyboardInterrupt:
            # TODO: Move this into the cli, ``KeyboardInterrupt`` handling
            # should be taken care of by the client. Also you should be allowed
            # to disable this.
            os.remove(filepath)
            raise KeyboardInterrupt(
                "Interrupt signal given. Deleting incomplete video.")   
        return 
        
    
    def run(self):

        global queue
        counter = 0
        videosurl = []
        
        if 'playlist?list' in link.get():
            videosurl = self.playlistvideo()
        else:
            videosurl.append(link.get())
    
        for i in videosurl:
            counter = counter + 1
            msg = str(counter) + " of " + str(len(videosurl))            
            self.videodownload(i , msg)
            
                  
  
def enabled () :
    videoFormat.config(state = NORMAL)        
    box.config(state = NORMAL)              
    link.config(state = NORMAL)                
    Save.config(state = NORMAL)                 
    startDownload.config(state = NORMAL)                    
    #About.config(state = 'active')                
    #Exit.config(state = 'active') 

def disabled () :
    videoFormat.config(state = DISABLED)        
    box.config(state = DISABLED)              
    link.config(state = DISABLED)                
    Save.config(state = DISABLED)                 
    startDownload.config(state = DISABLED)                    
    #About.config(state = 'disabled')                
    #Exit.config(state = 'disabled') 

def sizeof(byts):
    """Takes the size of file or folder in bytes and returns size formatted in
    KB, MB, GB, TB or PB.
    :params byts:
        Size of the file in bytes
    """
    byts = int(byts)
    sizes = ['bytes', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb']
    if(byts != 0):
        power = int(math.floor(math.log(byts, 1024)))
        notation = int(byts/float(1024**power)) 
        
    else:
        power = 0
        notation = 0
    suffix = sizes[power] if byts != 1 else 'byte'
    return '{0} {1}'.format(notation, suffix)

def sizeofspeed(byts):
    """Takes the size of file or folder in bytes and returns size formatted in
    KB, MB, GB, TB or PB.
    :params byts:
        Size of the file in bytes
    """
    byts = int(byts)
    sizes = ['bytes', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb']
    if(byts != 0):
        power = int(math.floor(math.log(byts, 1024)))
        notation = round((byts/float(1024**power)) ,1 ) 
        
    else:
        power = 0
        notation = 0
    suffix = sizes[power] if byts != 1 else 'byte'
    return '{0} {1}'.format(notation, suffix)


def download():
    """Downloads the video.

    :param str path:
        The destination output directory.
    :param int chunk_size:
        File size (in bytes) to write to buffer at a time. By default,
        this is set to 8 bytes.
    :param func on_progress:
        *Optional* function to be called every time the buffer is written
        to. Arguments passed are the bytes recieved, file size, and start
        datetime.
    :param func on_finish:
        *Optional* callback function when download is complete. Arguments
        passed are the full path to downloaded the file.
    :param bool force_overwrite:
        *Optional* force a file overwrite if conflicting one exists.
    """
    disabled() 
    thread = ThreadedClient()
    thread.daemon = True
    thread.start()
    periodicCall(thread)

def periodicCall(thread):
    global root  
    checkqueue()
    if thread.is_alive():
        root.after(100 , periodicCall , thread)
    else:
        enabled()


def checkqueue():
    global queue
    while(queue.qsize()):
        #print (queue.qsize())
        value = queue.get()
        if 'Downloading :' in value:
            About.config(text = value)
        else:            
            percantage.config(text=value)
            ETR.config(text = queue.get())
            progressBar.step(queue.get())
            progressBar.update_idletasks()
'''while(not queue.empty()):
    percantage.config(text=str(int((bytes_received*100)/file_size)) + "%")
    progressBar.step((100*progress)/(file_size + .0001))
    speed = round(bytes_received/(time.time() - start), 2)
    tR = (file_size-bytes_received)/speed
    string =( "Time Remaining : %.2f   Speed : %sps  Size : %s  Remaining : %s"  %(tR ,sizeof(speed) , sizeof(file_size) ,sizeof(file_size-bytes_received)))
    ETR.config(text = string )
    progressBar.update_idletasks()
    toggleFlag = queue.get(0)'''
        



def FilePath():
    global path
    path = filedialog.askdirectory(initialdir = '.')
    


videoFormat         = Label(root, text="Choose Video Format  :"  )
 
box                 = ttk.Combobox(root, textvariable=quality, state='readonly' , width =6 )

link                = Entry(root,width = 64 ,bd = 3);
Save                = Button(root, text ="...", command = FilePath , width=3 ,bd=1);

startDownload       = Button(root,text = "Start Download",command = download ,width=20 ,bd=2);


frame               = Frame(root)

progressBar         = ttk.Progressbar(frame ,orient='horizontal',length=393, mode='determinate' , maximum = 100.01)
percantage          = Label(frame)
ETR                 = Label(root )

About               = Label(root);
#Exit                = Button (root, text ="Exit",width=15,bd=2);


def main():
    global root;
    setwidgetlayout() ;
    root.mainloop();

if __name__ == '__main__':    main();
