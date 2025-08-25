import argparse
from pathlib import Path
from .config_loader import load_config, DEFAULT_CONFIG_PATH
from .logger import setup_logger
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
        print(f"Error: The source folder '{source_path}' does not exist.")
        return

    # Validate or create the target folder
    if not target_path.exists():
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"Created target folder: {target_path}")
        except Exception as e:
            print(f"Error creating target folder '{target_path}': {e}")
            return

    try:
        # Run the renamer function
        rename_photos(str(source_path), test_mode=test_mode, verbose=verbose)

        # Skip the mover function if in test mode
        if test_mode:
            print("Test mode enabled. The files are not actually renamed, so the mover function will skip the files.")

        # Run the mover function
        move_photos(str(source_path), str(target_path), test_mode=test_mode, verbose=verbose)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
def validate_cli_args(args, logger=None):
    """
    Validate CLI arguments and return structured config.
    """
    if not args.source_folder or not args.target_folder:
        raise ValueError("Both source and target folders must be provided via CLI.")

    source_folder = Path(args.source_folder).resolve()
    target_folder = Path(args.target_folder).resolve()

    if not source_folder.is_dir():
        raise FileNotFoundError(f"Source folder '{source_folder}' does not exist or is not a directory.")

    if logger:
        logger.info(f"CLI source folder: {source_folder}")
        logger.info(f"CLI target folder: {target_folder}")
        logger.info(f"Test mode: {args.test}")
        logger.info(f"Verbose mode: {args.verbose}")

    return {
        "source_folder": source_folder,
        "target_folder": target_folder,
        "test_mode": args.test,
        "verbose": args.verbose
    }

def validate_config(config, logger=None):
    """
    Validate config file contents and return structured config.
    """
    folders = config.get("folders", {})
    flags = config.get("flags", {})

    source_folder = Path(folders.get("source", "")).resolve()
    target_folder = Path(folders.get("target", "")).resolve()
    test_mode = flags.get("test")
    verbose = flags.get("verbose")

    if not source_folder or not target_folder:
        raise ValueError("Config file is missing 'folders.source' or 'folders.target'.")

    if not source_folder.is_dir():
        raise FileNotFoundError(f"Source folder '{source_folder}' does not exist or is not a directory.")

    if test_mode is None or verbose is None:
        raise ValueError("Config file is missing 'flags.test' or 'flags.verbose'.")

    if logger:
        logger.info(f"Config source folder: {source_folder}")
        logger.info(f"Config target folder: {target_folder}")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Verbose mode: {verbose}")

    return {
        "source_folder": source_folder,
        "target_folder": target_folder,
        "test_mode": test_mode,
        "verbose": verbose
    }

def validate_interactive_input(logger=None):
    """
    Prompt user for input interactively and return structured config.
    """
    source_folder = Path(input("Please enter the source folder: ").strip()).resolve()
    target_folder = Path(input("Please enter the target folder: ").strip()).resolve()

    if not source_folder.is_dir():
        raise FileNotFoundError(f"Source folder '{source_folder}' does not exist or is not a directory.")

    test_mode_input = input("Run in test mode? (y/n): ").lower()
    verbose_input = input("Display detailed output? (y/n): ").lower()
    test_mode = test_mode_input == 'y'
    verbose = verbose_input == 'y'

    if logger:
        logger.info(f"Interactive source folder: {source_folder}")
        logger.info(f"Interactive target folder: {target_folder}")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Verbose mode: {verbose}")

    return {
        "source_folder": source_folder,
        "target_folder": target_folder,
        "test_mode": test_mode,
        "verbose": verbose
    }

def main():
    """
    Main function to parse command-line arguments, load configuration,
    and invoke the bulk photo renamer and mover functions.
    """
    logger = None
    config = {}
    config_path = DEFAULT_CONFIG_PATH

    try:
        # Step 1: Load config if available (for logger setup only)
        if config_path.is_file():
            try:
                config = load_config(config_path)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
                config = {}
        else:
            print(f"Config file not found at {config_path}. Proceeding without it.")

        # Setup logger early using config or defaults
        logger_name = config.get('logger_name', 'bulk_photo_processor')
        log_file = config.get('log_file', 'logs/bulk_photo_processor.log')
        logger = setup_logger(logger_name, str(Path(log_file).resolve()))
        logger.info("Logger initialised.")

        # Step 2: Parse CLI arguments
        parser = argparse.ArgumentParser(description='Run bulk photo renamer and mover scripts.')
        parser.add_argument('-t', '--test', action='store_true', help='Test mode (only output results without renaming or moving files)')
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode (output results)')
        parser.add_argument('source_folder', type=str, nargs='?', help='Path to the source folder containing the images')
        parser.add_argument('target_folder', type=str, nargs='?', help='Path to the target folder')
        args = parser.parse_args()

        # Step 3: Determine mode based on CLI presence
        if args.source_folder or args.target_folder:
            validated = validate_cli_args(args, logger)
        elif config:
            validated = validate_config(config, logger)
        else:
            validated = validate_interactive_input(logger)

        # Final validation
        if not validated["target_folder"]:
            raise ValueError("Target folder is not specified.")

        # Run the main processing function
        logger.info("Bulk photo processing begins.")
        process_photos(
            str(validated["source_folder"]),
            str(validated["target_folder"]),
            validated["test_mode"],
            validated["verbose"]
        )

    except Exception as e:
        if logger:
            logger.error(f"Fatal error: {e}")
        print(f"Error: {e}")

if __name__ == '__main__':
    main()