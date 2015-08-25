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
import Tkconstants
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
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('TkAgg')
import os

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

stopped = False
EVENT_COUNT = 20
def update_ui(queue,LOG_FILE_NAME,graph_queue):
	global stopped,EVENT_COUNT
	
	#setup logging
	foregroundLogger = logging.getLogger("ForegroundLogger")
	foregroundLogger.setLevel(logging.INFO)
	handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes= 10240)
	foregroundLogger.addHandler(handler)
	
	old_window = ""
	old_time = datetime.now()
	count_updates = 0
	screen = wnck.screen_get_default()
	screen.force_update()
	event_count = 10
	x = [(i+1) for i in range(event_count)]
	xlabels = ['' for i in range(event_count)]
	y = [0 for i in range(event_count)]
	c = ['g' for i in range(event_count)]
	while True:
	
		# obtain current active window
		while gtk.events_pending():
			gtk.main_iteration()
		active_window_name = screen.get_active_window().get_name()
		current_time = datetime.now()
		new_data = str(current_time)+" :: "+old_window
		
		#print "RAW stream:",new_data
		if(active_window_name != old_window and new_data != None):
			
			elapsed_time = (current_time - old_time).total_seconds()
			
			queue.put(new_data+' ['+str("%.2f" % round(elapsed_time/60.0,4))+' minutes ]')	
						
			if(elapsed_time > 1):  #consider only those switches with more than 1 s times
				# obtain the data for graph update
				
				xlabels = []
				for i in range(event_count-1):
					y[i] = y[i+1]
					c[i] = c[i+1]
				
				y[event_count-1] = elapsed_time/60.0
				if(old_window.find('Facebook') >= 0):
					c[event_count-1] = 'r'
				elif(old_window.find('Firefox') >= 0):
					c[event_count-1] = 'b'
				else:
					c[event_count-1] = 'g'
				graph_queue.put((x,y,xlabels,c))
			old_window = active_window_name
			old_time = current_time

			foregroundLogger.info(new_data+' ['+str("%.2f" % round(elapsed_time/60.0,4))+' minutes ]') # write name of active window to logfile
			if(stopped):
				break
		
		time.sleep(0.5)

class Gui(object):
	def __init__(self, queue,graph_queue):
		self.queue = queue
		self.graph_queue = graph_queue
		self.root = Tk()
		self.root.wm_title("Time Keeper System")
		#self.root.minsize(400,400)
		
		self.text1 = Text(self.root, height=10, width=20)
		self.photo=PhotoImage(file='/home/debjyoti/dev/utilities/clock.png')
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
		self.text2.insert(END,quote, 'color')
		self.text2.pack(side=BOTTOM)
		self.text2.insert(END,"\n", 'color')
		
		#code for the graph
		
		self.figure = Figure(figsize=(2,2), dpi=100)
		self.ax = self.figure.add_subplot(111)
		rects1 = self.ax.bar([] , [])
		self.ax.set_xticks([])
		self.ax.set_yticks([])
		self.ax.set_ylabel("Time in minutes")


		#a tk.DrawingArea
		self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
		self.canvas.show()
		self.canvas.get_tk_widget().pack(side='right', fill='both', expand=1)
                self.updateCount = 0
                print "start monitoring and updating the GUI"

		# Schedule read_queue to run in the main thread in one second.
		self.root.after(1000, self.read_queue)
		self.root.after(1000, self.read_graph_queue)

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
	
	def read_graph_queue(self):
		""" Check for updated temp data"""
		try:
			(x,y,xlabels,c) = self.graph_queue.get_nowait()	
			#update graph
			self.ax.clear()
			rects1 = self.ax.bar(x, y, 0.35, color=c)
			self.ax.set_xticks(x)
			#self.ax.set_xticklabels(xlabels)
			self.figure.canvas.draw()
			
			
		except Queue.Empty:
			# It's ok if there's no data to read.
			# We'll just check again later.
			pass
		# Schedule read_graph_queue again in one second.
		self.root.after(1000, self.read_graph_queue)	

		
		
		
	

if __name__ == "__main__":
	queue = Queue.Queue()
	graph_queue = Queue.Queue()
	# Start background thread to get temp data
	t = threading.Thread(target=update_ui, args=(queue,"timeKeeper.log",graph_queue))
	t.start()

	print "starting Timekeeper"
	# Build GUI object
	gui = Gui(queue,graph_queue)
	# Start mainloop
	gui.root.mainloop()
	stopped = True
	print "TimeKeeper terminated"
