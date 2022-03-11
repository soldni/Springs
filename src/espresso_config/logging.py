import logging
import os
from multiprocessing import current_process

from .utils import mkdir_p


def configure_logging(
    file_logging_path: str = None,
    make_dir_if_missing: bool = True,
    fmt: str = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
    logging_level: int = logging.INFO,
    force_root_reattach: bool = True,
    root_formatter_kwargs: dict = None,
    stream_handler_kwargs: dict = None,
    file_handler_kwargs: dict = None,
    basic_config_kwargs: dict = None,
    additional_handlers: list = None,
):
    """A big function that speeds up configuration of logging"""

    # change how the formatter looks
    kw = root_formatter_kwargs or {}
    root_formatter = logging.Formatter(fmt=fmt, datefmt=datefmt, **kw)

    handlers = list(additional_handlers or [])

    kw = stream_handler_kwargs or {}
    root_stream_handler = logging.StreamHandler(**kw)
    root_stream_handler.setFormatter(root_formatter)
    handlers.append(root_stream_handler)

    if file_logging_path is not None:
        path_dir, path_name = os.path.split(file_logging_path)

        path_dir = mkdir_p(path_dir) if make_dir_if_missing else path_dir

        path_name, path_ext = os.path.splitext(path_name)
        path_name = f'{path_name}_{current_process().name}{path_ext}'

        kw = file_handler_kwargs or {}
        root_file_handler = logging.FileHandler(
            filename=os.path.join(path_dir, path_name), **kw)
        root_file_handler.setFormatter(root_formatter)
        handlers.append(root_file_handler)

    # add the handlers to the root logger, force reattaching other loggers
    kw = basic_config_kwargs or {}
    logging.basicConfig(level=logging_level,
                        force=force_root_reattach,
                        handlers=handlers, **kw)