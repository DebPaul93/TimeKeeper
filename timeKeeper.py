'''
    File name: timeKeeper.py
    Author: Debjyoti Bhattacharjee
    Date created: 24/08/2015
    Date last modified: 24/08/2015
    Python Version: 2.7
    Description : The utility logs the current window name into 
    a log file "timeKeeper.log".
'''
from Tkinter import *
import tkFont
import os
import glob
import time
import threading
import Image 
import Queue
import wnck,gtk
import glob
import logging
import logging.handlers
from datetime import datetime

stopped = False
def update_ui(queue,LOG_FILE_NAME):
	global stopped
	
	#setup logging
	foregroundLogger = logging.getLogger("ForegroundLogger")
	foregroundLogger.setLevel(logging.INFO)
	handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes= 10240)
	foregroundLogger.addHandler(handler)
	
	old_window = ""
	count_updates = 0
	screen = wnck.screen_get_default()
	screen.force_update()
	
	while True:
	
		# obtain current active window
		while gtk.events_pending():
			gtk.main_iteration()
		active_window_name = screen.get_active_window().get_name()
		
		new_data = str(datetime.now())+" :: "+active_window_name
		
		#print "RAW stream:",new_data
		if(active_window_name != old_window and new_data != None):
			queue.put(new_data) # place name of active window in queue
			old_window = active_window_name
			if(count_updates == 100):
				print "Write to file"
				
				
			count_updates = count_updates + 1
			foregroundLogger.info(new_data) # write name of active window to logfile
			if(stopped):
				break
		
		time.sleep(0.5)

class Gui(object):
	def __init__(self, queue):
		self.queue = queue
		self.root = Tk()
		self.root.wm_title("Time Keeper System")
		#self.root.minsize(400,400)
		
		self.text1 = Text(self.root, height=20, width=30)
		self.photo=PhotoImage(file='./200.gif')
		self.text1.insert(END,'\n')
		self.text1.image_create(END, image=self.photo)

		self.text1.pack(side=LEFT)
		self.text1.config(state = DISABLED)

		self.text2 = Text(self.root, height=20, width=100)
		scroll = Scrollbar(self.root, command=self.text2.yview)
		self.text2.configure(yscrollcommand=scroll.set)
		self.text2.tag_configure('bold_italics', font=('Arial', 12, 'bold', 'italic'))
		self.text2.tag_configure('big', font=('Verdana', 20, 'bold'))
		self.text2.tag_configure('color', foreground='#476042', 
		font=('Tempus Sans ITC', 12, 'bold'))
		self.text2.tag_bind('follow', '<1>', lambda e, t=self.text2: t.insert(END, "Not now, maybe later!"))
		self.text2.insert(END,'\nWilliam Shakespeare\n', 'big')
		quote = """
		To be, or not to be that is the question:
		Whether 'tis Nobler in the mind to suffer
		The Slings and Arrows of outrageous Fortune,
		Or to take Arms against a Sea of troubles,
		"""
		self.text2.insert(END, quote, 'color')
		self.text2.pack(side=LEFT)
		self.text2.config(state = DISABLED)
		scroll.pack(side=RIGHT, fill=Y)
		
		self.updateCount = 0
		print "start monitoring and updating the GUI"

		# Schedule read_queue to run in the main thread in one second.
		self.root.after(1000, self.read_queue)

	def read_queue(self):
		""" Check for updated temp data"""
		try:
			new_data = self.queue.get_nowait()
			self.text2.configure(state='normal')
			self.text2.insert(END, new_data+"\n", 'red')
			self.text2.configure(state=DISABLED)
			if(self.updateCount == 100): #Clear Window
				self.text2.delete(1.0,END)
				self.updateCount = 0
			self.updateCount = self.updateCount + 1
			
		except Queue.Empty:
			# It's ok if there's no data to read.
			# We'll just check again later.
			pass
		# Schedule read_queue again in one second.
		self.root.after(1000, self.read_queue)


if __name__ == "__main__":
	queue = Queue.Queue()
	# Start background thread to get temp data
	t = threading.Thread(target=update_ui, args=(queue,"timeKeeper.log",))
	t.start()

	print "starting app"
	# Build GUI object
	gui = Gui(queue)
	# Start mainloop
	gui.root.mainloop()
	stopped = True
