import os


class Config:
    CONFIG_PATH = os.environ.get('CONFIG_PATH').replace("\n", "\\n").replace("\\", "/")
    BASE_ELEMENT = os.environ.get('BASE_ELEMENT', default='Root_object_type')


if __name__ == "__main__":
    en_vars = [attr for attr in dir(Config) if not callable(getattr(Config(), attr)) and not attr.startswith("__")]
    indent = max([len(el) for el in en_vars]) + 2
    [print((el + ":").ljust(indent, " ") + getattr(Config, el)) for el in en_vars]

    print(Config.CONFIG_PATH)