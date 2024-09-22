import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from acquire import start_recording

class App:
    def __init__(self):
        self.window = ttk.Window(themename="darkly")
        self.window.title('Camera Recording')
        self.window.geometry('500x400')
        self.window.resizable(False, False)  # make window non resizable
        
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Helvetica', 12))
        self.style.configure('TButton', font=('Helvetica', 12))
        self.style.configure('TCheckbutton', font=('Helvetica', 12))
        self.initUI()

    def initUI(self):
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=BOTH, expand=YES)

        # set title
        title_label = ttk.Label(main_frame, text="MoSeq - Orbbec Data Acquisition", font=('Helvetica', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # set subject name
        ttk.Label(main_frame, text='Subject Name:').grid(row=1, column=0, sticky=E, padx=5, pady=5)
        self.subject_input = ttk.Entry(main_frame, width=30)
        self.subject_input.grid(row=1, column=1, sticky=W, padx=5, pady=5)

        # set sesison name
        ttk.Label(main_frame, text='Session Name:').grid(row=2, column=0, sticky=E, padx=5, pady=5)
        self.session_input = ttk.Entry(main_frame, width=30)
        self.session_input.grid(row=2, column=1, sticky=W, padx=5, pady=5)

        # set directory
        ttk.Label(main_frame, text='Directory:').grid(row=3, column=0, sticky=E, padx=5, pady=5)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=3, column=1, sticky=W)
        self.dir_input = ttk.Entry(dir_frame, width=25)
        self.dir_input.pack(side=LEFT, fill=X, expand=YES)
        dir_button = ttk.Button(dir_frame, text='Browse', command=self.browse_directory, style='Outline.TButton')
        dir_button.pack(side=LEFT, padx=(5, 0))

        # recording length
        ttk.Label(main_frame, text='Recording Length (minutes):').grid(row=4, column=0, sticky=E, padx=5, pady=5)
        self.length_input = ttk.Entry(main_frame, width=10)
        self.length_input.insert(0, '20')
        self.length_input.grid(row=4, column=1, sticky=W, padx=5, pady=5)

        # checkboxes
        self.save_ir_var = tk.BooleanVar(value=True)
        self.save_ir_checkbox = ttk.Checkbutton(main_frame, text='Save IR', variable=self.save_ir_var, style='TCheckbutton')
        self.save_ir_checkbox.grid(row=5, column=0, sticky=W, padx=5, pady=10)
        self.preview_var = tk.BooleanVar(value=True)
        self.preview_checkbox = ttk.Checkbutton(main_frame, text='Show Preview', variable=self.preview_var, style='TCheckbutton')
        self.preview_checkbox.grid(row=5, column=1, sticky=W, padx=5, pady=10)

        # start button
        start_button = ttk.Button(main_frame, text='Start Recording', command=self.start_recording, style='success.TButton')
        start_button.grid(row=6, column=0, columnspan=2, pady=20)

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

        # destroy window
        self.window.destroy()

        # start recording
        start_recording(
            base_dir=directory,
            subject_name=subject_name,
            session_name=session_name,
            recording_length=recording_length * 60,  # Convert to seconds
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
