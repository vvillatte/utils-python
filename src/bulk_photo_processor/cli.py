import argparse
from pathlib import Path

from .bulk_photo_processor import process_photos
from .bulk_photo_renamer import rename_photos
from .bulk_photo_mover import move_photos
from .config_loader import load_config, DEFAULT_CONFIG_PATH
from .logger import setup_logger


# ------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------
def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Bulk photo renamer + mover. Renames files and organises them into YYYY/MM folders."
    )

    parser.add_argument(
        "-s", "--source-folder",
        type=str,
        help="Source folder containing photos."
    )

    parser.add_argument(
        "-d", "--destination-folder",
        type=str,
        help="Destination folder for organised photos."
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to a JSON config file, or 'default' to use the default config."
    )

    parser.add_argument(
        "-t", "--test",
        action="store_true",
        help="Test mode (simulate operations)."
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output."
    )

    parser.add_argument(
        "-ro", "--rename-only",
        action="store_true",
        help="Only rename photos in place."
    )

    parser.add_argument(
        "-mo", "--move-only",
        action="store_true",
        help="Only move photos without renaming."
    )

    return parser.parse_args()


# ------------------------------------------------------------
# Validation helpers
# ------------------------------------------------------------
def validate_source_and_target(source: Path, target: Path):
    if not source or not source.is_dir():
        raise FileNotFoundError(f"Source folder '{source}' does not exist or is not a directory.")

    if not target:
        raise ValueError("Destination folder must be provided.")

    if not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create destination folder '{target}': {e}")

    return source, target


# ------------------------------------------------------------
# Mode 1: CLI mode (strict)
# ------------------------------------------------------------
def try_cli_mode(args, logger):
    if not args.source_folder and not args.destination_folder:
        return None  # CLI mode not triggered

    if args.source_folder and not args.destination_folder:
        raise ValueError("Destination folder is missing. Both source and destination must be provided.")

    if args.destination_folder and not args.source_folder:
        raise ValueError("Source folder is missing. Both source and destination must be provided.")

    logger.info("CLI mode selected.")

    source = Path(args.source_folder).resolve()
    target = Path(args.destination_folder).resolve()

    validate_source_and_target(source, target)

    return {
        "source_folder": source,
        "target_folder": target,
        "test_mode": args.test,
        "verbose": args.verbose,
    }


# ------------------------------------------------------------
# Mode 2: Config mode
# ------------------------------------------------------------
def try_config_mode(args, logger):
    config_path = None

    if args.config:
        logger.info("Config mode selected via CLI.")

        if args.config == "default":
            config_path = DEFAULT_CONFIG_PATH
        else:
            config_path = Path(args.config)

        if not config_path.is_file():
            raise FileNotFoundError(f"Config file '{config_path}' does not exist.")

    else:
        if DEFAULT_CONFIG_PATH.is_file():
            logger.info("Default config file detected. Using config mode.")
            config_path = DEFAULT_CONFIG_PATH
        else:
            return None  # No config available

    config = load_config(config_path)

    folders = config.get("folders", {})
    flags = config.get("flags", {})

    source = Path(folders.get("source", "")).resolve()
    target = Path(folders.get("target", "")).resolve()

    validate_source_and_target(source, target)

    if "test" not in flags or "verbose" not in flags:
        raise ValueError("Config file missing required flags: 'test' and 'verbose'.")

    mode = config.get("mode", "full")
    if mode not in ("full", "rename-only", "move-only"):
        raise ValueError("Invalid mode in config file. Must be 'full', 'rename-only', or 'move-only'.")

    return {
        "source_folder": source,
        "target_folder": target,
        "test_mode": flags["test"],
        "verbose": flags["verbose"],
        "mode": mode,
    }


# ------------------------------------------------------------
# Mode 3: Interactive mode
# ------------------------------------------------------------
def interactive_mode(logger):
    print("No CLI parameters or valid config detected.")
    print("Choose mode:")
    print("A) Configuration file")
    print("B) Parameters")

    choice = input("Select A or B: ").strip().lower()

    if choice == "a":
        logger.info("Interactive mode: configuration file selected.")

        use_default = input("Use default config? (y/n): ").strip().lower()

        if use_default == "y":
            config_path = DEFAULT_CONFIG_PATH
            if not config_path.is_file():
                raise FileNotFoundError("Default config file does not exist.")
        else:
            config_path_str = input("Enter path to config file: ").strip()
            if not config_path_str:
                raise ValueError("No config file path provided.")
            config_path = Path(config_path_str)
            if not config_path.is_file():
                raise FileNotFoundError(f"Config file '{config_path}' does not exist.")

        config = load_config(config_path)
        folders = config.get("folders", {})
        flags = config.get("flags", {})

        source = Path(folders.get("source", "")).resolve()
        target = Path(folders.get("target", "")).resolve()

        validate_source_and_target(source, target)

        return {
            "source_folder": source,
            "target_folder": target,
            "test_mode": flags.get("test", False),
            "verbose": flags.get("verbose", False),
        }


    elif choice == "b":
        logger.info("Interactive mode: manual parameters selected.")
        source = Path(input("Enter source folder: ").strip()).resolve()
        target = Path(input("Enter destination folder: ").strip()).resolve()
        validate_source_and_target(source, target)
        test_mode = input("Test mode? (y/n): ").strip().lower() == "y"
        verbose = input("Verbose mode? (y/n): ").strip().lower() == "y"
        print("Choose operation mode:")
        print("1) Rename only")
        print("2) Move only")
        print("3) Full pipeline (rename + move)")
        mode_choice = input("Select 1, 2, or 3: ").strip()
        if mode_choice == "1":
            mode = "rename-only"
        elif mode_choice == "2":
            mode = "move-only"
        elif mode_choice == "3":
            mode = "full"
        else:
            raise ValueError("Invalid selection. Choose 1, 2, or 3.")
        return {
            "source_folder": source,
            "target_folder": target,
            "test_mode": test_mode,
            "verbose": verbose,
            "mode": mode,
        }

    else:
        raise ValueError("Invalid selection. Choose A or B.")


# ------------------------------------------------------------
# Top-level CLI entry point
# ------------------------------------------------------------
def cli():
    args = parse_cli_args()

    # Setup logger early
    logger = setup_logger("bulk_photo_processor", "logs/bulk_photo_processor.log")
    logger.info("CLI started.")

    # Mode 1: CLI mode
    try:
        config = try_cli_mode(args, logger)
        if config:
            logger.info("Running in CLI mode.")
            # ------------------------------------------------------------
            # Rename-only / Move-only logic (CLI overrides config)
            # ------------------------------------------------------------
            if args.rename_only and args.move_only:
                raise ValueError("Cannot use --rename-only and --move-only together.")

            # CLI overrides config
            if args.rename_only:
                logger.info("Running in rename-only mode (CLI override).")
                rename_photos(
                    str(config["source_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            if args.move_only:
                logger.info("Running in move-only mode (CLI override).")
                move_photos(
                    str(config["source_folder"]),
                    str(config["target_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            # ------------------------------------------------------------
            # No CLI override → use config mode
            # ------------------------------------------------------------
            mode = config.get("mode", "full")

            if mode == "rename-only":
                logger.info("Running in rename-only mode (config).")
                rename_photos(
                    str(config["source_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            if mode == "move-only":
                logger.info("Running in move-only mode (config).")
                move_photos(
                    str(config["source_folder"]),
                    str(config["target_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            # Default: full pipeline
            logger.info("Running full rename + move pipeline.")
            process_photos(**config)
            return
    except Exception as e:
        logger.error(f"CLI mode error: {e}")
        raise

    # Mode 2: Config mode
    try:
        config = try_config_mode(args, logger)
        if config:
            logger.info("Running in config mode.")

            # ------------------------------------------------------------
            # Rename-only / Move-only logic (CLI overrides config)
            # ------------------------------------------------------------
            if args.rename_only and args.move_only:
                raise ValueError("Cannot use --rename-only and --move-only together.")

            # CLI overrides config
            if args.rename_only:
                logger.info("Running in rename-only mode (CLI override).")
                rename_photos(
                    str(config["source_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            if args.move_only:
                logger.info("Running in move-only mode (CLI override).")
                move_photos(
                    str(config["source_folder"]),
                    str(config["target_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            # ------------------------------------------------------------
            # No CLI override → use config mode
            # ------------------------------------------------------------
            mode = config.get("mode", "full")

            if mode == "rename-only":
                logger.info("Running in rename-only mode (config).")
                rename_photos(
                    str(config["source_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            if mode == "move-only":
                logger.info("Running in move-only mode (config).")
                move_photos(
                    str(config["source_folder"]),
                    str(config["target_folder"]),
                    test_mode=config["test_mode"],
                    verbose=config["verbose"]
                )
                return

            # Default: full pipeline
            logger.info("Running full rename + move pipeline.")
            process_photos(**config)
            return
    except Exception as e:
        logger.error(f"Config mode error: {e}")
        raise

    # Mode 3: Interactive mode
    try:
        config = interactive_mode(logger)
        logger.info("Running in interactive mode.")

        # ------------------------------------------------------------
        # Rename-only / Move-only logic (CLI overrides config)
        # ------------------------------------------------------------
        if args.rename_only and args.move_only:
            raise ValueError("Cannot use --rename-only and --move-only together.")

        # CLI overrides config
        if args.rename_only:
            logger.info("Running in rename-only mode (CLI override).")
            rename_photos(
                str(config["source_folder"]),
                test_mode=config["test_mode"],
                verbose=config["verbose"]
            )
            return

        if args.move_only:
            logger.info("Running in move-only mode (CLI override).")
            move_photos(
                str(config["source_folder"]),
                str(config["target_folder"]),
                test_mode=config["test_mode"],
                verbose=config["verbose"]
            )
            return

        # ------------------------------------------------------------
        # No CLI override → use config mode
        # ------------------------------------------------------------
        mode = config.get("mode", "full")

        if mode == "rename-only":
            logger.info("Running in rename-only mode (config).")
            rename_photos(
                str(config["source_folder"]),
                test_mode=config["test_mode"],
                verbose=config["verbose"]
            )
            return

        if mode == "move-only":
            logger.info("Running in move-only mode (config).")
            move_photos(
                str(config["source_folder"]),
                str(config["target_folder"]),
                test_mode=config["test_mode"],
                verbose=config["verbose"]
            )
            return

        # Default: full pipeline
        logger.info("Running full rename + move pipeline.")
        process_photos(**config)

    except Exception as e:
        logger.error(f"Interactive mode error: {e}")
        raise
