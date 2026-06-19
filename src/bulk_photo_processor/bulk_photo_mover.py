import re
import hashlib
from pathlib import Path
from tqdm import tqdm
from colorama import Fore, Style


def calculate_checksum(file_path, algorithm='md5'):
    """Calculate the checksum of a file using the specified algorithm."""
    hash_alg = hashlib.new(algorithm)
    try:
        with Path(file_path).open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_alg.update(chunk)
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {file_path}: {e}")
    return hash_alg.hexdigest()


def move_photos(source_folder, target_folder, test_mode=False, verbose=False):
    """Move photos from source to destination, organizing by year/month."""
    source_path = Path(source_folder).resolve()
    target_path = Path(target_folder).resolve()

    if not source_path.is_dir():
        raise FileNotFoundError(f"Source directory '{source_path}' does not exist or is not a directory.")

    try:
        target_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Error creating destination directory '{target_path}': {e}")

    try:
        files = [entry for entry in source_path.iterdir() if entry.is_file()]
    except Exception as e:
        raise RuntimeError(f"Error accessing files in source directory '{source_path}': {e}")

    valid_extensions = {'.jpg', '.jpeg', '.png', '.mpg', '.mp4', '.avi', '.heic'}
    pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})T(\d{2})_(\d{2})_(\d{2})-\d{6}.*\..*')
    files_to_move = [f for f in files if pattern.match(f.name) and f.suffix.lower() in valid_extensions]

    if not files_to_move:
        if verbose:
            print("No files matching the pattern were found.")
        return

    pbar = tqdm(
        total=len(files_to_move),
        ncols=70,
        bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)
    )

    for file in files_to_move:
        try:
            match = pattern.match(file.name)
            if not match:
                continue

            year, month, *_ = match.groups()
            subfolder_path = target_path / year / month
            subfolder_path.mkdir(parents=True, exist_ok=True)

            target_file_path = subfolder_path / file.name
            target_file_path = target_file_path.with_suffix(target_file_path.suffix.lower())

            if target_file_path.exists():
                # Check for duplicate
                if (
                    file.stat().st_size == target_file_path.stat().st_size and
                    calculate_checksum(file) == calculate_checksum(target_file_path)
                ):
                    if verbose:
                        print(f"Duplicate file found and discarded: {file}")
                    continue

                # Generate unique filename
                counter = 1
                while True:
                    new_file_name = f"{file.stem}_{counter:02}{file.suffix.lower()}"
                    new_target_file_path = subfolder_path / new_file_name
                    if not new_target_file_path.exists():
                        target_file_path = new_target_file_path
                        break
                    counter += 1

            if test_mode or verbose:
                print(f"{file} --> {target_file_path}")

            if not test_mode:
                file.rename(target_file_path)

            pbar.update(1)

        except Exception as e:
            raise RuntimeError(f"Error moving file '{file}': {e}")

    pbar.close()
