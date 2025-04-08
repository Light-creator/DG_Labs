import winreg
import argparse
import os
import shutil

# File Section
def write_file(file_name: str, value: str) -> None:
    with open(file_name, "a") as f:
        f.write(value)

def create_file(file_name: str) -> None:
    try:
        f = open(file_name, "x")
        f.close()
    except FileExistsError:
        raise FileExistsError(f"File {file_name} already exists")

def delete_file(file_name: str) -> None:
    try:
        os.remove(file_name)
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_name} not found")

def read_file(file_name: str) -> None:
    try:
        with open(file_name, "r") as f:
            print(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_name} not found")

def copy_file(file_name: str, new_file_path: str) -> None:
    try:
        shutil.copyfile(file_name, new_file_path)
    except shutil.SameFileError:
        raise shutil.SameFileError(f"Files names should be different")
    except OSError as err:
        raise OSError(f"File {new_file_path} already exists")

def rename_file(file_name: str, new_file_name: str) -> None:
    try:
        os.rename(file_name,  new_file_name)
    except FileExistsError:
        raise FileNotFoundError(f"File {new_file_name} already exists")
    except IsADirectoryError:
        raise IsADirectoryError(f"File {new_file_name} is a directory")

def search_str(path: str, value: str) -> None:
    try:
        walker = os.walk(path)
        for (dirpath, dirnames, filenames) in walker:
            for file_name in filenames:
                file_path = os.path.join(dirpath, file_name)
                with open(file_path, "r", encoding="cp1252", errors="ignore") as f:
                    if value in f.read(): 
                        print(f"Value {value} was found in {file_path}")
    except OSError as err:
        raise("Invalid or inaccessible file names and paths")


def file_helper(args: argparse.Namespace) -> None:
    if args.operation == "write":
        write_file(args.name, args.value)
    elif args.operation == "create":
        create_file(args.name)
    elif args.operation == "delete":
        delete_file(args.name)
    elif args.operation == "copy":
        copy_file(args.name, args.dst)
    elif args.operation == "read":
        read_file(args.name)
    elif args.operation == "rename":
        rename_file(args.name, args.dst)
    elif args.operation == "search":
        search_str(args.dst, args.value)
    else:
        raise Exception(f"Unknown file operation: {args.operation}")

# Reg section
def create_key(location, key_name: str) -> None:
    try:
        key = winreg.CreateKeyEx(location, key_name, 0, winreg.KEY_ALL_ACCESS)
        winreg.CloseKey(key)
        winreg.CloseKey(location)
    except OSError:
        raise OSError(f"Failed to create key {location_name}\\{key_name}")


def delete_key(location, key_name: str) -> None:
    try:
        winreg.DeleteKeyEx(location, key_name)
        winreg.CloseKey(location)
    except OSError:
        raise OSError(f"Failed to delete key {location_name}\\{key_name}")

def set_value(location, key_name: str, value_name: str, value: str) -> None:
    try:
        key = winreg.OpenKeyEx(location, key_name, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        winreg.CloseKey(location)
    except OSError:
        raise OSError(f"Failed to set value key {location_name}\\{key_name} -> {value_name}={value}")

def enumerate_key_values(key, searched_value: str, location: str):
    idx = 0
    while True:
        try:
            value_name, value, value_type = winreg.EnumValue(key, idx)
            if value_type == winreg.REG_SZ and searched_value == value:
                print(f"Value {searched_value} was found in {location}: {value_name}")
            idx += 1
        except OSError as err:
            # No More Values
            return None

def search_reg_value(section: int, location: str, value: str, max_level: int, level: int):
    if level >= max_level: return None
    try:
        with winreg.OpenKeyEx(section, location, 0, winreg.KEY_READ) as key:
            enumerate_key_values(key, value, location)
            idx = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, idx)
                
                    if len(location) > 0: subkey_path = f"{location}\\{subkey}"
                    else: subkey_path = subkey

                    search_reg_value(section, subkey_path, value, max_level, level+1)
            
                    idx += 1
                except OSError as err:
                    break
    except OSError as err:
        # Failed to get handle
        return None

def reg_helper(args: argparse.Namespace) -> None:
    section = winreg.HKEY_CLASSES_ROOT
    if args.section == 'HKCU':
        section = winreg.HKEY_CURRENT_USER
    elif args.section == 'HKU':
        section = winreg.HKEY_USERS
    elif args.section == 'HKLM':
        section = winreg.HKEY_LOCAL_MACHINE
    elif args.section == 'HKCR':
        section = winreg.HKEY_CLASSES_ROOT
    elif args.section == 'HCC':
        section = winreg.HKEY_CURRENT_CONFIG
    else:
        raise Exception(f"Unknown registry section type: {args.section}")
    
    if args.operation == "search":
        search_reg_value(section, "", args.value, 5, 0)
        return
    
    location = None
    try:
        location = winreg.OpenKeyEx(section, args.location, 0, winreg.KEY_ALL_ACCESS)
    except OSError:
        raise OSError(f"Failed to get handle of {args.location}")


    if args.operation == 'create':
        create_key(location, args.name)
    elif args.operation == 'set':
        set_value(location, args.name, args.value_name, args.value)
    elif args.operation == 'delete':
        delete_key(location, args.name)
    else:
        raise Exception(f"Unknown operation for registry: {args.operation}")

def helper(args: argparse.Namespace) -> None:
    if args.operation_type == 'file':
        file_helper(args)
    elif args.operation_type == 'reg':
        reg_helper(args)
    else:
        raise Exception("Unknown operation type: Should be file or reg")

def main() -> None:
    parser = argparse.ArgumentParser(description='UTILS')
    parser.add_argument('operation_type', type=str, help='operation type (file or reg)')
    parser.add_argument('operation', type=str, help='operation (read, write...)')
    parser.add_argument('-s', '--section', type=str, help='section (HKEY_LOCAL_MACHINE)')
    parser.add_argument('-l', '--location', type=str, help='key location')
    parser.add_argument('-n', '--name', type=str, help='file or key name')
    parser.add_argument('-v', '--value', type=str, help='value for file write or key value')
    parser.add_argument('-vn', '--value_name', type=str, help='value name for key')
    parser.add_argument('-d', '--dst', type=str, help='destination path')
    args = parser.parse_args()
    
    if not args.operation_type:
        raise Exception("Operation type argument is required")
    
    if not args.operation:
        raise Exception("Operation argument is required")

    if args.operation_type == "file":
        if args.operation == "write" and not args.value:
            raise Exception("Value argument is required for write file operation")
        if args.operation == "copy" and not args.dst:
            raise Exception("Dst argument is required for copy operation")
        if args.operation == "rename" and not args.dst:
            raise Exception("Dst argument is required for rename operation")
    
    if args.operation_type == "reg":
        if not args.section:
            raise Exception("Section argument is required for reg operation type")

        if args.operation == "set" and not args.value:
            raise Exception("Value argument is required for set operation")
        if args.operation == "set" and not args.value_name:
            raise Exception("Value name argument is required for set operation")

    helper(args)

if __name__ == "__main__":
    main()
