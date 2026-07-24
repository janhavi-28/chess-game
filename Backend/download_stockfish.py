import urllib.request
import zipfile
import os
import shutil

print("Downloading Stockfish...")
url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-windows-x86-64-avx2.zip"
zip_path = "stockfish.zip"
urllib.request.urlretrieve(url, zip_path)

print("Extracting Stockfish...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    # find the exe file in the zip
    exe_name = next((name for name in zip_ref.namelist() if name.endswith(".exe")), None)
    if exe_name:
        print(f"Found executable: {exe_name}")
        zip_ref.extract(exe_name, ".")
        shutil.move(exe_name, "stockfish.exe")
        print("Moved to stockfish.exe")
    else:
        print("Could not find .exe in zip")

if os.path.exists(zip_path):
    os.remove(zip_path)
