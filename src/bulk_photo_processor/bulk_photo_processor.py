from pathlib import Path
from .bulk_photo_renamer import rename_photos
from .bulk_photo_mover import move_photos


def process_photos(source_folder, target_folder, test_mode, verbose):
    """
    Process photos by renaming and moving them.
    """
    source_path = Path(source_folder).resolve()
    target_path = Path(target_folder).resolve()

    # Validate the source folder
    if not source_path.is_dir():
        raise FileNotFoundError(f"Source folder '{source_path}' does not exist or is not a directory.")

    # Validate or create the target folder
    if not target_path.exists():
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"Created target folder: {target_path}")
        except Exception as e:
            raise RuntimeError(f"Error creating target folder '{target_path}': {e}")

    # Run the renamer function
    rename_photos(str(source_path), test_mode=test_mode, verbose=verbose)

    # Skip the mover function if in test mode
    if test_mode:
        if verbose:
            print("Test mode enabled. Files will not be renamed or moved.")
        return

    # Run the mover function
    move_photos(str(source_path), str(target_path), test_mode=test_mode, verbose=verbose)
