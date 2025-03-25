import winreg
import argparse
import os

#  def create_key(location: winreg.HKEYType, key_name: str) -> None:
#      key = winreg.CreateKeyEx(location, key_name)
#
#  def helper(args: argparse.Namespace) -> None:
#      location = winreg.HKEY_LOCAL_MACHINE
#      print(args.next_location)
#      new_loc = winreg.OpenKeyEx(location, args.next_location)
#      create_key(new_loc, "KEY")
#
#      value_handle = winreg.SetValueEx(key, "VAL", 0, winreg.REG_SZ, "qwe val qwe")
#

def write_file(file_name: str, value: str) -> None:
    try:
        with open(file_name, "w") as f:
            f.write(value)
    except Exception as err:
        raise Exception(f"Failed to write file {file_name}: {err}")

def create_file(file_name: str) -> None:
    try:
        f = open(file_name, "w")
        f.close()
    except Exception as err:
        raise Exception(f"Failed to create file {file_name}: {err}")

def delete_file(file_name: str) -> None:
    try:
        os.remove(file_name)
    except OSError as err:
        raise Exception(f"Failed to delete file {file_name}: {err}")

def rename_file(file_name: str, new_file_name: str):
    try:
        os.rename(file_name, new_file_name)
    except OSError as err:
        raise Exception(f"Failed to rename file {file_name} -> {new_file_name}: {err}")



def file_helper(args: argparse.Namespace) -> None:
    if args.operation == "write":
        write_file(args.name, args.value)
    elif args.operation == "create":
        create_file(args.name)
    elif args.operation == "delete":
        delete_file(args.name)

def create_key(section: int, location_name: str, key_name: str) -> None:
    try:
        location = winreg.OpenKeyEx(section, location_name, 0, winreg.KEY_ALL_ACCESS)
        key = winreg.CreateKeyEx(location, key_name, 0, winreg.KEY_ALL_ACCESS)
        winreg.CloseKey(key)
        winreg.CloseKey(location)
    except WindowsError as err:
        raise WindowsError(f"Failed to create key {location_name}\\{key_name}: {err}")


def delete_key(section: int, location_name: str, key_name: str) -> None:
    try:
        location = winreg.OpenKeyEx(section, location_name, 0, winreg.KEY_ALL_ACCESS)
        winreg.DeleteKeyEx(location, key_name)
        winreg.CloseKey(location)
    except WindowsError as err:
        raise WindowsError(f"Failed to delete key {location_name}\\{key_name}: {err}")

def set_value(section: int, location_name: str, key_name: str, value_name: str, value: str) -> None:
    try:
        location = winreg.OpenKeyEx(section, location_name, 0, winreg.KEY_ALL_ACCESS)
        key = winreg.OpenKeyEx(location, key_name, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        winreg.CloseKey(location)
    except WindowsError as err:
        raise WindowsError(f"Failed to set value key {location_name}\\{key_name} -> {value_name}={value}: {err}")


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

    if args.name == None:
        raise Exception(f"Key should be initialized")

    if args.location == None:
        raise Exception(f"Location should be initialized")

    if args.operation == 'create':
        create_key(section, args.location_name, args.name)
    elif args.operation == 'set':
        set_value(section, args.location_name, args.name, args.value_name, args.value)
    elif args.operation == 'delete':
        delete_key(section, args.location_name, args.name)
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
    args = parser.parse_args()
        
    helper(args)

if __name__ == "__main__":
    main()
