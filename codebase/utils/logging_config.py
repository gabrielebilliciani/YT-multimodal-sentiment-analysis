import logging
import sys

def setup_logging(level=logging.INFO):
    """Configures basic logging for the application."""
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-5.5s] [%(name)s] [%(threadName)s]  %(message)s"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Optional: File Handler
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(log_formatter)
    # root_logger.addHandler(file_handler)

    print("Logging configured.")

# Example of how you might use it in other modules:
# import logging
# logger = logging.getLogger(__name__) # Use module name for logger
# logger.info("This is an info message from my_module.")