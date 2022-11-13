def get_order_directory_recursively(directory: dict):
    new_dict = dict(sorted({**directory}.items()))
    for (key, value) in new_dict.items():
        if type(value) is dict:
            new_dict[key] = get_order_directory_recursively(
                value)
    return new_dict
