import os
import logging
import colorlog


def get_logging_config(log_dir, log_file_name='app.log'):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'color': {
                '()': 'colorlog.ColoredFormatter',
                'format': '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'log_colors': {
                    'DEBUG': 'white',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'color',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'formatter': 'standard',
                'filename': os.path.join(log_dir, log_file_name),
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True
            },
            'my_module': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False
            },
            'aiormq.connection': {
                'handlers': ['console', 'file'],
                'level': 'ERROR',
                'propagate': False
            },
        }
    }
