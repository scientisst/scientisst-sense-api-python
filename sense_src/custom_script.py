import os
import sys
import importlib.util
from sense_src.thread_builder import ThreadBuilder


class CustomScript(ThreadBuilder):
    def __init__(self):
        super().__init__()
        self.on_init()

    def start(self):
        super().start()
        self.on_start()

    def stop(self):
        super().stop()
        self.on_stop()

    def thread_method(self, frames):
        self.on_read(frames)

    def on_init(self):
        pass

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_read(self, frames):
        pass


def get_custom_script(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    if "_" in module_name:
        module_name = "".join([word.capitalize() for word in module_name.split("_")])
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        CustomScript = getattr(module, module_name)
        return CustomScript()
    except AttributeError:
        print("%s: No such class." % module_name, file=sys.stderr)
        exit(1)
