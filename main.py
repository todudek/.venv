import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import astropy.units as u
from sunpy.net import Fido, attrs as a
from sunpy.map import Map
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from astropy.wcs import WCS

# Funkcja pomocnicza do pobierania i wyświetlania obrazów
def fetch_and_display_images(start_date, end_date, time_str, wavelength, frame, progress, show_button):
    wavelength_unit = int(wavelength) * u.angstrom
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    delta = end_dt - start_dt

    total_images = delta.days + 1
    progress['maximum'] = total_images

    fetched_files = []

    for i in range(total_images):
        day = start_dt + timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        time_range = a.Time(f'{date_str}T{time_str}', f'{date_str}T{time_str}')
        print(f"Pobieranie danych dla {date_str} i długości fali {wavelength}Å...")
        result = Fido.search(time_range, a.Instrument("aia"), a.Wavelength(wavelength_unit))
        
        if len(result) > 0:
            files = Fido.fetch(result[0, 0])  # Pobiera pierwszy dostępny obraz z wyników
            fetched_files.extend(files)
            print(f"Pobrano {len(files)} obraz(ów) dla {date_str}.")
        else:
            print(f"Brak danych dla {date_str}.")

        progress['value'] = i + 1
        frame.update_idletasks()

    # Uaktywnienie przycisku "Pokaż zdjęcia" po zakończeniu pobierania
    show_button['state'] = 'normal'
    show_button['command'] = lambda: display_images(fetched_files, frame)

def display_images(image_paths, frame):
    for widget in frame.winfo_children():
        widget.destroy()
    for file_path in image_paths:
        sun_map = Map(file_path)
        wcs = WCS(sun_map.wcs.to_header())
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1, projection=wcs)
        sun_map.plot(axes=ax)
        ax.set_xlim(0, sun_map.data.shape[1])
        ax.set_ylim(0, sun_map.data.shape[0])

        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        img_array = np.array(canvas.buffer_rgba())
        img = Image.fromarray(img_array)
        img_tk = ImageTk.PhotoImage(img)
        panel = tk.Label(frame, image=img_tk)
        panel.image = img_tk  # Zapobiega garbage-collection
        panel.pack(side="left", padx=5, pady=5)

# Główna klasa aplikacji
class SDOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SDO Image Viewer")
        self.geometry("800x600")  # Rozmiar okna

        self.wavelength_options = ['94', '131', '171', '193', '211', '304', '335', '1600', '1700', '4500', '6173']

        # Podział okna na dwie części
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X)
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        self.define_top_frame_elements(top_frame)
        self.image_frame = bottom_frame

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
        self.wavelength_combobox.pack(side="left", fill=tk.X, expand=True)
        self.wavelength_combobox.set('171')

        self.progress = ttk.Progressbar(top_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side="left", padx=10)

        ttk.Button(top_frame, text="OK", command=self.on_ok).pack(side="left")
        self.show_button = ttk.Button(top_frame, text="Pokaż zdjęcia", state='disabled')
        self.show_button.pack(side="left")

    def on_ok(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        time_str = self.time_entry.get()
        wavelength = self.wavelength_var.get()
        fetch_and_display_images(start_date, end_date, time_str, wavelength, self.image_frame, self.progress, self.show_button)

if __name__ == "__main__":
    app = SDOApp()
    app.mainloop()
