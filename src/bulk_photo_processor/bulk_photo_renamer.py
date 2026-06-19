import re
from pathlib import Path
from tqdm import tqdm
from colorama import Fore, Style


def rename_photos(directory, test_mode=False, verbose=False):
    """
    Renames files from 'YYYYMMDD_HHMMSS.ext' to 'YYYY-MM-DDTHH_MM_SS-000001.ext'.
    """
    dir_path = Path(directory).resolve()

    if not dir_path.is_dir():
        raise FileNotFoundError(f"Directory '{dir_path}' does not exist or is not a directory.")

    try:
        files = [f for f in dir_path.iterdir() if f.is_file()]
    except Exception as e:
        raise RuntimeError(f"Error accessing files in directory '{dir_path}': {e}")

    pattern = re.compile(r'\d{8}_\d{6}.*\..*')
    files_to_rename = [f for f in files if pattern.match(f.name)]

    if not files_to_rename:
        if verbose:
            print("No files matching the pattern were found.")
        return

    pbar = tqdm(
        total=len(files_to_rename),
        ncols=70,
        bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)
    )

    file_count = 0

    for file in files_to_rename:
        try:
            base_name = file.stem
            ext = file.suffix.lower()

            # Extract the timestamp portion
            base_name = re.sub(r'(\d{8}_\d{6}).*', r'\1', base_name)
            date, time = base_name.split('_')

            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            formatted_time = f"{time[:2]}_{time[2:4]}_{time[4:6]}"

            file_count += 1
            new_name = f"{formatted_date}T{formatted_time}-{file_count:06}{ext}"
            new_path = dir_path / new_name

            if new_path.exists():
                raise FileExistsError(f"Target file '{new_path}' already exists.")

            if test_mode or verbose:
                print(f"{file} --> {new_path}")

            if not test_mode:
                file.rename(new_path)

            pbar.update(1)

        except Exception as e:
            raise RuntimeError(f"Error renaming file '{file}': {e}")

    pbar.close()
