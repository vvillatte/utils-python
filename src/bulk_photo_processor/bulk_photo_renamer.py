import sys
import re
from pathlib import Path
from tqdm import tqdm
from colorama import Fore, Style, init

def rename_photos(directory, test_mode=False, verbose=False):
    """
    Renames files from 'YYYYMMDD_HHMMSS.ext' to 'YYYY-MM-DDTHH_MM_SS-000001.ext'.

    Args:
        directory (str): Path to the directory containing files.
        test_mode (bool): If True, simulate renaming.
        verbose (bool): If True, print detailed output.
    """
    dir_path = Path(directory)

    if not dir_path.is_dir():
        print(f"Error: The directory {directory} does not exist.")
        return

    try:
        files = [f for f in dir_path.iterdir() if f.is_file()]
    except Exception as e:
        print(f"Error accessing files in directory: {e}")
        return

    pattern = re.compile(r'\d{8}_\d{6}.*\..*')
    files_to_rename = [f for f in files if pattern.match(f.name)]

    if not files_to_rename:
        print("No files matching the pattern were found.")
        return

    pbar = tqdm(total=len(files_to_rename), ncols=70,
                bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL))

    file_count = 0

    for file in files_to_rename:
        try:
            base_name = file.stem
            ext = file.suffix.lower()

            base_name = re.sub(r'(\d{8}_\d{6}).*', r'\1', base_name)
            date, time = base_name.split('_')
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            formatted_time = f"{time[:2]}_{time[2:4]}_{time[4:6]}"
            file_count += 1

            new_name = f"{formatted_date}T{formatted_time}-{file_count:06}{ext}"
            new_path = dir_path / new_name

            if new_path.exists():
                print(f"Error: The file {new_path} already exists.")
                continue

            if test_mode or verbose:
                print(f"{file} --> {new_path}")

            if not test_mode:
                file.rename(new_path)

            pbar.update(1)
        except Exception as e:
            print(f"Error renaming file {file}: {e}")

    pbar.close()

def main():
    # Initialize colorama
    init(autoreset=True)

    args = sys.argv[1:]

    if args and args[0].startswith('-'):
        switches = args[0]
        directory = args[1] if len(args) > 1 else input("Please enter the directory where the photos are located: ")

        test_mode = 't' in switches
        verbose = 'v' in switches
    else:
        directory = input("Please enter the directory where the photos are located: ")
        test_mode = input("Do you want to run in test mode? (y/n): ").lower() == 'y'
        verbose = input("Do you want to display detailed output? (y/n): ").lower() == 'y'

    rename_photos(directory, test_mode, verbose)

if __name__ == "__main__":
    main()
