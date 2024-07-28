import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from acquire import start_recording
import os
from PIL import Image, ImageTk

class App:
    def __init__(self):
        self.window = ttk.Window(themename="darkly")
        self.window.title('Camera Recording')
        self.window.geometry('500x400')

        icon_path = "/home/llorentelab/icon.png"  
        icon = Image.open(icon_path)
        icon = ImageTk.PhotoImage(icon)
        self.window.iconphoto(True, icon)

        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Clam', 12))
        self.style.configure('TButton', font=('Clam', 12))
        self.style.configure('TCheckbutton', font=('Clam', 12))
        self.initUI()

    def initUI(self):
        main_frame = ttk.Frame(self.window, padding="20 20 20 20")
        main_frame.pack(fill=BOTH, expand=YES)

        # set title
        title_label = ttk.Label(main_frame, text="Orbbec Data Acquisition", font=('Clam', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        # set subject name
        subject_frame = ttk.Frame(main_frame)
        subject_frame.pack(fill=X, pady=5)
        ttk.Label(subject_frame, text='Subject Name:').pack(side=LEFT)
        self.subject_input = ttk.Entry(subject_frame, width=30)
        self.subject_input.pack(side=RIGHT)

        # set session name
        session_frame = ttk.Frame(main_frame)
        session_frame.pack(fill=X, pady=5)
        ttk.Label(session_frame, text='Session Name:').pack(side=LEFT)
        self.session_input = ttk.Entry(session_frame, width=30)
        self.session_input.pack(side=RIGHT)

        # directory
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=X, pady=5)
        ttk.Label(dir_frame, text='Directory:').pack(side=LEFT)
        self.dir_input = ttk.Entry(dir_frame, width=30)
        self.dir_input.pack(side=LEFT, expand=YES, fill=X, padx=(0, 5))
        dir_button = ttk.Button(dir_frame, text='Browse', command=self.browse_directory, style='Outline.TButton')
        dir_button.pack(side=RIGHT)

        # set recording length
        length_frame = ttk.Frame(main_frame)
        length_frame.pack(fill=X, pady=5)
        ttk.Label(length_frame, text='Recording Length (minutes):').pack(side=LEFT)
        self.length_input = ttk.Entry(length_frame, width=10)
        self.length_input.insert(0, '20')
        self.length_input.pack(side=RIGHT)

        # checkboxes
        checks_frame = ttk.Frame(main_frame)
        checks_frame.pack(fill=X, pady=10)
        self.save_ir_var = tk.BooleanVar(value=True)
        self.save_ir_checkbox = ttk.Checkbutton(checks_frame, text='Save IR', variable=self.save_ir_var, style='TCheckbutton')
        self.save_ir_checkbox.pack(side=LEFT, padx=(0, 20))
        self.preview_var = tk.BooleanVar(value=True)
        self.preview_checkbox = ttk.Checkbutton(checks_frame, text='Show Preview', variable=self.preview_var, style='TCheckbutton')
        self.preview_checkbox.pack(side=LEFT)

        # start button
        start_button = ttk.Button(main_frame, text='Start Recording', command=self.start_recording, style='success.TButton')
        start_button.pack(pady=20)

    def browse_directory(self):
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.dir_input.delete(0, tk.END)
            self.dir_input.insert(0, dir_name)

    def start_recording(self):
        subject_name = self.subject_input.get()
        session_name = self.session_input.get()
        directory = self.dir_input.get()
        try:
            recording_length = float(self.length_input.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for recording length.")
            return
        save_ir = self.save_ir_var.get()
        preview = self.preview_var.get()

        if not all([subject_name, session_name, directory]):
            messagebox.showerror("Missing Information", "Please fill in all fields.")
            return

        # Close the window
        self.window.destroy()

        # start the recording
        start_recording(
            base_dir=directory,
            subject_name=subject_name,
            session_name=session_name,
            recording_length=recording_length * 60,  #convert to seconds
            save_ir=save_ir,
            display_frames=preview,
            display_time=True,
            depth_height_threshold=150
        )

def main():
    gui = App()
    gui.window.mainloop()

if __name__ == '__main__':
    main()
