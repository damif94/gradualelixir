import os
import sys

from dotenv import find_dotenv, load_dotenv, set_key, get_key

dotenv_path = find_dotenv()
dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.dirname(dir_path)
dir_path = os.path.dirname(dir_path)
set_key(dotenv_path, "PROJECT_PATH", dir_path)
load_dotenv(dotenv_path)

if get_key(dotenv_path, 'DEV') == 'True':
    sys.path.insert(0, os.path.join(dir_path, 'src'))
