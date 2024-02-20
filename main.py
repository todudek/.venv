import astropy.units as u
from sunpy.net import Fido, attrs as a
from sunpy.map import Map
import matplotlib.pyplot as plt
from datetime import datetime, timedelta  # Dodano import timedelta
import os

# Funkcja do tworzenia pliku tekstowego z informacjami o obrazie
def create_image_info_file(file_path, sun_map):
    info_file_path = f"{file_path}.txt"
    with open(info_file_path, "w") as f:
        f.write(f"Nazwa obrazu: {os.path.basename(file_path)}\n")
        f.write(f"Czas wykonania zdjęcia: {sun_map.date.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Zakres: {sun_map.wavelength}\n")
    print(f"Utworzono plik z informacjami: {info_file_path}")

# Funkcja do pobierania danych dla określonych dat
def download_sdo_images(dates, time_str):
    downloaded_files = []

    for date_str in dates:
        # Tworzy pełną datę i czas dla zapytania
        query_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        time_range = a.Time(query_datetime, query_datetime + timedelta(minutes=1))

        # Wyszukuje dane z instrumentu AIA/SDO
        result = Fido.search(time_range, a.Instrument("aia"), a.Wavelength(171 * u.angstrom))

        # Pobiera dane
        if len(result) > 0:
            files = Fido.fetch(result[0, 0])  # Pobiera pierwszy dostępny obraz z wyników
            downloaded_files.extend(files)
        else:
            print(f"Nie znaleziono danych dla {query_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    return downloaded_files

# Funkcja do wyświetlania pobranych obrazów i tworzenia plików z informacjami
def display_images_and_create_info_files(files):
    for file in files:
        sun_map = Map(file)
        plt.figure()
        sun_map.plot()
        plt.colorbar()
        plt.title(f"SDO AIA 171 Å - {sun_map.date.strftime('%Y-%m-%d %H:%M:%S')}")
    plt.show()  # Wyświetla wszystkie obrazy naraz po zakończeniu pętli

    for file in files:
        sun_map = Map(file)
        create_image_info_file(file, sun_map)

# Główna część programu
if __name__ == "__main__":
    # Lista dat dla pobierania obrazów
    dates = ["2023-01-10", "2023-01-30", "2023-02-15"]
    time_str = "07:30"  # Stała godzina dla wszystkich dat

    # Pobieranie obrazów
    downloaded_files = download_sdo_images(dates, time_str)

    # Wyświetlanie obrazów i tworzenie plików z informacjami
    display_images_and_create_info_files(downloaded_files)
