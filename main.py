import tkinter as tk
from tkinter import ttk, simpledialog
from datetime import datetime, timedelta
import astropy.units as u
from sunpy.net import Fido, attrs as a
from sunpy.map import Map
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SDOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SDO Image Viewer")
        self.geometry("1000x800")

        self.wavelength_options = ['94', '131', '171', '193', '211', '304', '335', '1600', '1700', '4500', '6173']
        self.fetched_files = []
        self.image_dates = {}
        self.image_canvas_refs = []

        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X)
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)

        self.define_top_frame_elements(top_frame)

    def define_top_frame_elements(self, top_frame):
        tk.Label(top_frame, text="Start Date (YYYY-MM-DD):").pack(side="left")
        self.start_date_entry = ttk.Entry(top_frame)
        self.start_date_entry.pack(side="left")

        tk.Label(top_frame, text="End Date (YYYY-MM-DD):").pack(side="left")
        self.end_date_entry = ttk.Entry(top_frame)
        self.end_date_entry.pack(side="left")

        tk.Label(top_frame, text="Time (HH:MM):").pack(side="left")
        self.time_entry = ttk.Entry(top_frame)
        self.time_entry.pack(side="left")

        tk.Label(top_frame, text="Wavelength (Å):").pack(side="left")
        self.wavelength_var = tk.StringVar()
        self.wavelength_combobox = ttk.Combobox(top_frame, textvariable=self.wavelength_var, values=self.wavelength_options)
        self.wavelength_combobox.pack(side="left", expand=True)
        self.wavelength_combobox.set('171')

        self.progress = ttk.Progressbar(top_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side="left", padx=10)

        ttk.Button(top_frame, text="Fetch Images", command=self.on_ok).pack(side="left")
        self.show_images_button = ttk.Button(top_frame, text="Show Images", state='disabled', command=self.display_fetched_images)
        self.show_images_button.pack(side="left")
        self.label_button = ttk.Button(top_frame, text="Label Images", state='disabled', command=self.start_labeling)
        self.label_button.pack(side="left")

    def on_ok(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        time_str = self.time_entry.get()
        wavelength = self.wavelength_var.get()
        self.fetch_images(start_date, end_date, time_str, wavelength)

    def fetch_images(self, start_date, end_date, time_str, wavelength):
        wavelength_unit = int(wavelength) * u.angstrom
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_dt - start_dt

        total_images = delta.days + 1
        self.progress['maximum'] = total_images

        for i in range(total_images):
            day = start_dt + timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            time_range = a.Time(f'{date_str}T{time_str}', f'{date_str}T{time_str}')
            result = Fido.search(time_range, a.Instrument("aia"), a.Wavelength(wavelength_unit))
            
            if len(result) > 0:
                files = Fido.fetch(result[0, 0])
                for file in files:
                    self.fetched_files.append(file)
                    self.image_dates[file] = f"{date_str} {time_str}"

            self.progress['value'] = i + 1
            self.update_idletasks()

        if self.fetched_files:
            self.show_images_button['state'] = 'normal'

    def display_fetched_images(self):
        for file_path in self.fetched_files:
            sun_map = Map(file_path)
            fig, ax = plt.subplots(figsize=(5, 4), subplot_kw={'projection': sun_map.wcs})
            sun_map.plot(axes=ax)
            ax.set_xlim(0, sun_map.data.shape[1])
            ax.set_ylim(0, sun_map.data.shape[0])

            canvas = FigureCanvasTkAgg(fig, master=self.bottom_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side="left", fill="both", expand=True)
            canvas.draw()

            self.image_canvas_refs.append(canvas)
            self.image_dates[canvas] = self.image_dates[file_path]

        self.label_button['state'] = 'normal'

    def start_labeling(self):
        for canvas in self.image_canvas_refs:
            canvas.mpl_connect("button_press_event", self.on_press)
            canvas.mpl_connect("button_release_event", self.on_release)

    def on_press(self, event):
        self.rect_start = (event.xdata, event.ydata)

    def on_release(self, event):
        if not self.rect_start or not event.xdata or not event.ydata:
            return
        rect_end = (event.xdata, event.ydata)
        x0, y0 = self.rect_start
        x1, y1 = rect_end

        for canvas in self.image_canvas_refs:
            if event.inaxes in canvas.figure.axes:
                ax = event.inaxes
                rect = plt.Rectangle((min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0), linewidth=1, edgecolor='r', facecolor='none')
                rect_patch = ax.add_patch(rect)
                canvas.draw()

                comment = simpledialog.askstring("Label Comment", "Enter a comment for the label:")
                if comment is None:  # User clicked "Cancel"
                    rect_patch.remove()
                    canvas.draw()
                    return

                self.save_label_to_file(comment, x0, y0, x1, y1, self.image_dates[canvas])
                self.display_comment_and_coords(comment, x0, y0, x1, y1)

    def save_label_to_file(self, comment, x0, y0, x1, y1, image_date_time):
        with open("labels.txt", "a") as file:
            file.write(f"Date/Time: {image_date_time}, Comment: {comment}, Coordinates: ({x0:.2f}, {y0:.2f}), ({x1:.2f}, {y1:.2f})\n")

    def display_comment_and_coords(self, comment, x0, y0, x1, y1):
        label_frame = tk.Frame(self.bottom_frame)
        label_frame.pack(fill=tk.X)
        label_text = f"Comment: {comment} | Coordinates: x0={x0:.2f}, y0={y0:.2f}, x1={x1:.2f}, y1={y1:.2f}"
        tk.Label(label_frame, text=label_text, fg="red").pack()

if __name__ == "__main__":
    app = SDOApp()
    app.mainloop()
