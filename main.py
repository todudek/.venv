import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import astropy.units as u
from sunpy.net import Fido, attrs as a
from sunpy.map import Map
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from astropy.wcs import WCS
from sunpy.net import hek

class SDOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SDO Image Viewer")
        self.geometry("800x600")
        self.first_click = True

        self.define_gui_elements()

    def define_gui_elements(self):
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(fill=tk.X)
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.top_frame, text="Start Date (YYYY-MM-DD):").pack(side="left")
        self.start_date_entry = ttk.Entry(self.top_frame)
        self.start_date_entry.pack(side="left")

        tk.Label(self.top_frame, text="End Date (YYYY-MM-DD):").pack(side="left")
        self.end_date_entry = ttk.Entry(self.top_frame)
        self.end_date_entry.pack(side="left")

        tk.Label(self.top_frame, text="Time (HH:MM):").pack(side="left")
        self.time_entry = ttk.Entry(self.top_frame)
        self.time_entry.pack(side="left")

        self.wavelength_var = tk.StringVar()
        self.wavelength_combobox = ttk.Combobox(self.top_frame, textvariable=self.wavelength_var, state="readonly")
        self.wavelength_combobox.pack(side="left", fill=tk.X, expand=True)

        ttk.Button(self.top_frame, text="OK", command=self.on_ok).pack(side="left")
        self.progress = ttk.Progressbar(self.top_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side="left", padx=10)

    def on_ok(self):
        if self.first_click:
            self.check_available_wavelengths()
        else:
            self.fetch_images()

    def check_available_wavelengths(self):
        start_date = self.start_date_entry.get() + "T" + self.time_entry.get()
        end_date = self.end_date_entry.get() + "T" + self.time_entry.get()
        time_range = a.Time(start_date, end_date)

        # Wykonanie zapytania do Fido
        result = Fido.search(time_range, a.Instrument("AIA"))

        # Wydobycie unikalnych długości fal z wyników
        unique_waves = set()
        for response in result:
            for item in response:
                # Uzyskanie długości fali z obiektu item
                if hasattr(item, 'wave'):
                    wave_str = str(item.wave)
                    # Usuwanie niechcianych znaków
                    wave_str = wave_str.replace('[', '').replace(']', '').replace('A', '').split()[0]
                    unique_waves.add(wave_str)

        if unique_waves:
            # Konwersja set na listę, sortowanie i aktualizacja combobox
            try:
                unique_waves = sorted(list(unique_waves), key=lambda x: float(x))
                # Wyświetlanie informacji o znalezionych długościach fal w terminalu
                print("Znalezione dostępne długości fal: ", unique_waves)
            except ValueError as e:
                print(f"Error converting wavelength to float: {e}")
                return

            self.wavelength_combobox['values'] = [f"{wave} Å" for wave in unique_waves]
            self.wavelength_combobox.set(unique_waves[0] + ' Å')
            self.first_click = False  # Umożliwienie drugiego kroku
        else:
            messagebox.showinfo("Info", "No data available for the selected date and time.")


    def fetch_images(self):
        start_date = self.start_date_entry.get() + "T" + self.time_entry.get()
        end_date = self.end_date_entry.get() + "T" + self.time_entry.get()
        time_range = a.Time(start_date, end_date)
        wavelength = self.wavelength_var.get() + "A"

        query = Fido.search(
            time_range,
            a.Instrument("AIA"),
            a.Wavelength(wavelength)
        )
        downloaded_files = Fido.fetch(query)

        self.display_images(downloaded_files)

    def display_images(self, image_paths):
        for widget in self.bottom_frame.winfo_children():
            widget.destroy()
        for image_path in image_paths:
            sun_map = Map(image_path)
            wcs = WCS(sun_map.wcs.to_header())
            fig = Figure(figsize=(4, 4))
            ax = fig.add_subplot(1, 1, 1, projection=wcs)
            sun_map.plot(axes=ax)
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            img_array = np.array(canvas.buffer_rgba())
            img = Image.fromarray(img_array)
            img_tk = ImageTk.PhotoImage(img)
            panel = tk.Label(self.bottom_frame, image=img_tk)
            panel.image = img_tk
            panel.pack(side="left", padx=5, pady=5)

if __name__ == "__main__":
    app = SDOApp()
    app.mainloop()
