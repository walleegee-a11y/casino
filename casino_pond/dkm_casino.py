#!/usr/local/bin/python3.12

import os
import re
import argparse
import subprocess
import getpass
from prettytable import PrettyTable

# -----------------------------------------------------------------------------
# 1. Initialize environment variables and define default .hier paths
# -----------------------------------------------------------------------------
pond_var = os.getenv('casino_pond')
if not pond_var:
    print("Environment variable 'casino_pond' is not set. Exiting.")
    exit(1)

# By default, we assume these files exist in your $casino_pond directory.
ws_hier_file_path = os.path.join(pond_var, 'ws_casino.hier')
dk_hier_file_path = os.path.join(pond_var, 'dk_casino.hier')
flow_default_file_path = os.path.join(pond_var, 'flow_casino.yaml')
flow_manager_file_path = os.path.join(pond_var, 'fm_casino.py')


# -----------------------------------------------------------------------------
# 2. Parse Categories from the .hier file (e.g., dk_casino.hier)
# -----------------------------------------------------------------------------
def parse_categories(hier_file_path):
    """
    Parses the hierarchy file to extract category names (e.g., 'design', 'std', etc.)
    located under the '-- imported' directory. This depends on how many dashes
    prefix each line. We look for lines at level 3 under imported (--- category).
    """
    categories = []
    in_imported = False
    try:
        with open(hier_file_path, 'r') as file:
            for line in file:
                stripped_line = line.strip()
                dash_match = re.match(r'^(-+)', stripped_line)
                if dash_match:
                    num_dashes = len(dash_match.group(1))
                    dir_name = stripped_line[num_dashes:].strip()

                    if num_dashes == 2 and dir_name == 'imported':
                        in_imported = True
                        continue
                    elif num_dashes <= 2:
                        in_imported = False

                    if in_imported and num_dashes == 3:
                        categories.append(dir_name)

        if not categories:
            print("No categories found under '-- imported' in the hierarchy file.")
            exit(1)
    except FileNotFoundError:
        print(f"Hierarchy file not found at: {hier_file_path}")
        exit(1)
    except Exception as e:
        print(f"Error parsing hierarchy file: {e}")
        exit(1)

    return categories


categories = parse_categories(dk_hier_file_path)
print(f"Parsed Categories: {categories}")


# -----------------------------------------------------------------------------
# Utility function to list existing directories for each category (global view)
# -----------------------------------------------------------------------------
def list_existing_dirs_for_categories(base_path, prj_name, categories):
    """
    Lists existing directories for each category under prj_name/dbs/imported.
    """
    table = PrettyTable()
    table.field_names = ["Category", "Existing Directories"]
    for cat in categories:
        cat_path = os.path.join(base_path, prj_name, "dbs", "imported", cat)
        if os.path.isdir(cat_path):
            dirs = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
            dir_str = ", ".join(dirs) if dirs else "None"
        else:
            dir_str = "Not Found"
        table.add_row([cat, dir_str])
    print("\nExisting directories for each category:")
    print(table)


# -----------------------------------------------------------------------------
# 3. Utility Functions
# -----------------------------------------------------------------------------
def detect_placeholder(directory):
    """
    Detect if the directory string contains the literal '$db_ver' part.
    """
    parts = directory.split('/')
    for part in parts:
        if part == "$db_ver":
            return part
    return None


def create_directory_structure(base_path, structure, custom_db_vers=None, create_dirs=True):
    """
    Reads a list of (level, dir_name) from a .hier file and creates directories
    in a hierarchical manner. If 'custom_db_vers' is set, we replace '$db_ver'
    where relevant.
    """
    current_paths = {0: base_path}
    level_4_dirs_created = []

    for level, dir_name in structure:
        placeholder = detect_placeholder(dir_name)

        if placeholder and custom_db_vers:
            parent_path = current_paths.get(level - 1, '')
            base_dir = os.path.basename(parent_path)
            if base_dir in custom_db_vers:
                dir_name = dir_name.replace(placeholder, custom_db_vers[base_dir])

        if dir_name.strip() == "":
            continue

        if level == 0:
            parent_path = base_path
        else:
            parent_path = current_paths.get(level - 1)
            if not parent_path:
                continue

        dir_path = os.path.join(parent_path, dir_name)

        if re.search(r'""', dir_path):
            print(f"Skipping directory creation due to empty placeholder: {dir_path}")
            continue

        if create_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                if level == 4:
                    level_4_dirs_created.append(dir_path)
            else:
                if level == 4:
                    print(f"Skipping creation, level 4 directory already exists: {dir_path}")

        current_paths[level] = dir_path

    if create_dirs and level_4_dirs_created:
        sorted_dirs = sorted(
            level_4_dirs_created,
            key=lambda path: categories.index(os.path.basename(os.path.dirname(path)))
            if os.path.basename(os.path.dirname(path)) in categories
            else len(categories)
        )

        table = PrettyTable()
        table.field_names = ["Directory Path", "Base Name"]
        table.align = "l"

        for d in sorted_dirs:
            base_name = os.path.basename(d)
            table.add_row([d, base_name])

        print("\nCreated directories at level 4 depth in the specified order:")
        print(table)

    return current_paths


def read_structure_from_file(file_path, db_ver, prj_name):
    """
    Reads lines from a .hier file, strips the leading dashes, calculates indentation,
    and optionally replaces '$db_ver' and '$prj' if needed.
    Returns a list of (indent_level, dir_name).
    """
    structure = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                stripped_line = re.sub(r'^\s*-+\s*', '', line.strip())
                indent_level = (len(line) - len(line.lstrip(' '))) // 4

                if db_ver:
                    stripped_line = stripped_line.replace("$db_ver", db_ver)
                stripped_line = stripped_line.replace("$prj", prj_name).replace('"', '')

                structure.append((indent_level, stripped_line))
    except FileNotFoundError:
        print(f"Hierarchy file not found at: {file_path}")
        exit(1)
    except Exception as e:
        print(f"Error reading hierarchy file: {e}")
        exit(1)
    return structure


def initialize_git_repo(base_path):
    """
    Initializes a Git repo at 'base_path', if none exists already.
    """
    git_dir = os.path.join(base_path, '.git')
    if not os.path.exists(git_dir):
        try:
            subprocess.run(['git', 'init'], cwd=base_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f'Initialized Git repository in {git_dir}')
        except subprocess.CalledProcessError as e:
            print(f"Error initializing Git repository: {e.stderr.decode().strip()}")
            exit(1)
    else:
        print(f'Git repository already exists in {git_dir}')


def detect_db_ver_depth(structure):
    """
    Looks for the first line that contains '$db_ver' in the .hier structure,
    returns its indent level or 4 if not found.
    """
    for level, dir_name in structure:
        if '$db_ver' in dir_name:
            return level
    return 4


def display_existing_db_ver_dirs(base_path, structure, depth_level, prj_name, db_ver):
    """
    Prints out directories at the given 'depth_level' that might match '$db_ver'.
    Then calls prompt_for_db_ver which will list existing directories for each category
    before asking for input.
    """
    db_ver_dirs = []
    current_paths = {0: base_path}

    for level, dir_name in structure:
        if level == 0:
            parent_path = base_path
        else:
            parent_path = current_paths.get(level - 1)
            if parent_path is None:
                raise ValueError(f"Invalid hierarchy level: {level - 1}")
        dir_path = os.path.join(parent_path, dir_name)

        if level == depth_level:
            if os.path.isdir(dir_path):
                db_ver_dirs.append((dir_path, dir_name))

        current_paths[level] = dir_path

    if db_ver_dirs:
        table = PrettyTable()
        table.field_names = ["Index", "Directory Path", "Base Name"]
        table.align = "l"

        for idx, (d, original_name) in enumerate(db_ver_dirs, start=1):
            dir_base_name = os.path.basename(d)
            table.add_row([idx, d, dir_base_name])

        print(f"\nExisting directories at level {depth_level}:")
        print(table)
        return prompt_for_db_ver(categories, base_path, prj_name)
    else:
        print(f"No directories found at depth level {depth_level}.")
        return prompt_for_db_ver(categories, base_path, prj_name)


def prompt_for_db_ver(categories, base_path, prj_name):
    """
    For each category, display the existing directories from prj_name/dbs/imported/<category>
    so that the user can check before entering a new $db_ver value.
    Returns a dict {category: db_ver}.
    """
    custom_db_vers = {}
    print("\nPlease review existing directories for each category before entering a new $db_ver.\n")
    for cat in categories:
        cat_path = os.path.join(base_path, prj_name, "dbs", "imported", cat)
        if os.path.isdir(cat_path):
            dirs = [d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d))]
            if dirs:
                table = PrettyTable()
                table.field_names = [f"Existing dirs for '{cat}'"]
                for d in dirs:
                    table.add_row([d])
                print(f"\nExisting directories for {cat}, Enter db_ver:")
                print(table)
            else:
                print(f"\nNo existing directories found for category: {cat}")
        else:
            print(f"\nDirectory for category '{cat}' not found at: {cat_path}")
        print(f"Enter version for {cat}: ")
        ver = input().strip()
        if ver:
            custom_db_vers[cat] = ver
        else:
            print(f"No version entered for {cat}. Skipping.")
    if custom_db_vers:
        print("\nCustom $db_ver values entered:")
        ver_table = PrettyTable()
        ver_table.field_names = ["Category", "$db_ver"]
        for cat, ver in custom_db_vers.items():
            ver_table.add_row([cat, ver])
        print(ver_table)
    else:
        print("No custom $db_ver values entered. Exiting script.")
        exit(0)

    return custom_db_vers


def link_versions(base_path, ver_file, ver, prj_name, structure, custom_db_vers):
    """
    Creates symlinks from dbs/imported/<category>/<db_ver> to dbs/vers/<ver>/<category>.
    If ver_file doesn't exist, prompt user for each category version, create a
    new version directory, and link them.
    """
    while True:
        if os.path.exists(ver_file):
            print(f"{ver_file} exists.")
            print("Do you want to proceed with the existing version or provide a new one?")
            print("1. Proceed with the existing version.")
            print("2. Provide a new version name.")
            print("3. Overwrite the existing version.")
            selection = input().strip()

            if selection == '1':
                break
            elif selection == '2':
                print("Enter a new version name: ")
                ver = input().strip()
                if not ver:
                    print("No version entered. Please try again.")
                    continue
                test_ver_path = ver_file.replace('./ver.make', ver)
                if os.path.exists(test_ver_path):
                    print(f"Version '{ver}' already exists. Please choose another.")
                    continue
                break
            elif selection == '3':
                print(f"Overwriting the existing version '{ver}'.")
                vers_dir = os.path.join(base_path, prj_name, 'dbs', 'vers', ver)
                if os.path.exists(vers_dir):
                    try:
                        subprocess.run(['rm', '-rf', vers_dir], check=True)
                        print(f"Removed existing directory: {vers_dir}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error removing existing directory: {e.stderr.decode().strip()}")
                        exit(1)
                break
            else:
                print("Invalid selection. Please try again.")
        else:
            break

    if not os.path.exists(ver_file):
        print(f"{ver_file} not found. Please provide version details.\n")
        version_entries = {}
        for cat in categories:
            print(f"Enter version for {cat}: ")
            ver_input = input().strip()
            if ver_input:
                version_entries[cat] = ver_input

        if not version_entries:
            print("No version entries provided. Exiting script.")
            exit(0)

        current_paths = create_directory_structure(base_path, structure,
                                                   custom_db_vers,
                                                   create_dirs=False)

        dbs_path = None
        imported_path = None

        for level, dir_name in structure:
            parent_path = current_paths.get(level - 1, '')
            if dir_name == 'dbs':
                dbs_path = current_paths.get(level)
            if dir_name == 'imported':
                imported_path = current_paths.get(level)

        if not dbs_path:
            dbs_path = os.path.join(base_path, prj_name, 'dbs')
        if not imported_path:
            imported_path = os.path.join(dbs_path, 'imported')

        vers_dir = os.path.join(dbs_path, 'vers', ver)
        if os.path.exists(vers_dir):
            print(f"Version directory '{vers_dir}' already exists.")
            print("Do you want to overwrite it? (y/n): ")
            overwrite = input().strip().lower()
            if overwrite == 'y':
                try:
                    subprocess.run(['rm', '-rf', vers_dir], check=True)
                    print(f"Removed existing directory: {vers_dir}")
                except subprocess.CalledProcessError as e:
                    print(f"Error removing existing directory: {e.stderr.decode().strip()}")
                    exit(1)
            else:
                print("Please provide a different version name:")
                ver = input().strip()
                vers_dir = os.path.join(dbs_path, 'vers', ver)
                if os.path.exists(vers_dir):
                    print(f"Version '{ver}' already exists. Exiting script.")
                    exit(1)

        os.makedirs(vers_dir, exist_ok=True)

        linked_info_path = os.path.join(vers_dir, 'linked.info')
        with open(linked_info_path, 'w') as linked_info:
            for cat, db_ver in version_entries.items():
                src_path = os.path.join(imported_path, cat, db_ver)
                dest_path = os.path.join(vers_dir, cat)

                if os.path.islink(dest_path):
                    print(f"Skipping linking: {dest_path} already exists as a symlink.")
                else:
                    if os.path.exists(src_path):
                        if os.path.exists(dest_path):
                            try:
                                os.remove(dest_path)
                                print(f"Removed existing path: {dest_path}")
                            except Exception as e:
                                print(f"Error removing existing path {dest_path}: {e}")
                                continue
                        try:
                            os.symlink(src_path, dest_path)
                            link_cmd = f'ln -s {src_path} {dest_path}'
                            linked_info.write(f'{link_cmd}\n')
                            print(f'Linked {src_path} to {dest_path}')
                        except Exception as e:
                            print(f"Error creating symlink from {src_path} to {dest_path}: {e}")
                    else:
                        print(f"Source path {src_path} does not exist and cannot be linked.")
    else:
        pass


# -----------------------------------------------------------------------------
# New helper: Configure Git Identity using {whoami}@circling.co.kr
# -----------------------------------------------------------------------------
def configure_git_identity(repo_path):
    """
    Checks whether the local Git repository has user.email and user.name set.
    If not, automatically sets them using the current system username.
    The email is set to {username}@circling.co.kr and the name is set to the username.
    """
    result_email = subprocess.run(['git', 'config', '--get', 'user.email'],
                                  cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result_name = subprocess.run(['git', 'config', '--get', 'user.name'],
                                 cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if not result_email.stdout.strip() or not result_name.stdout.strip():
        username = getpass.getuser()
        email = f"{username}@circling.co.kr"
        name = username
        try:
            subprocess.run(['git', 'config', '--local', 'user.email', email],
                           cwd=repo_path, check=True)
            subprocess.run(['git', 'config', '--local', 'user.name', name],
                           cwd=repo_path, check=True)
            print(f"Git identity configured as {name} <{email}>.")
        except subprocess.CalledProcessError as e:
            print("Error configuring Git identity:", e.stderr.decode().strip())


# -----------------------------------------------------------------------------
# 4. Main CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Manage directory structure, linking, and Git (now with dbs).")
    parser.add_argument('-create_ver', action='store_true',
                        help="Prompt user to supply db_ver for each category and create directories.")
    parser.add_argument('-init_git', action='store_true',
                        help="Initialize Git in prj_name/dbs, checkout new branch, and commit.")
    parser.add_argument('-link_set', default='./ver.make', type=str,
                        help="Path to the ver.make file used in linking.")
    parser.add_argument('-link_ver', type=str,
                        help="Version name for linking (e.g., '31').")
    args = parser.parse_args()

    base_path = os.getcwd()
    prj_name = os.getenv('casino_prj_name')
    if not prj_name:
        print("Environment variable 'prj_name' is not set. Exiting.")
        exit(1)

    did_something = False

    if args.link_set and args.link_ver:
        structure = read_structure_from_file(dk_hier_file_path, None, prj_name)
        try:
            tree_path = os.path.join(prj_name, 'dbs', 'imported')
            subprocess.run(['tree', '-d', tree_path, '-L', '2'], check=True)
        except FileNotFoundError:
            print("The 'tree' command is not found. Please install it or ensure it's in the PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error displaying the directory tree: {e.stderr.decode().strip()}")
        list_existing_dirs_for_categories(base_path, prj_name, categories)
        print(f"Do you want to continue with linking ver {args.link_ver}? (y/n): ")
        proceed = input().strip().lower()
        if proceed != 'y':
            print("Exiting script.")
            exit(0)
        link_versions(base_path, args.link_set, args.link_ver, prj_name, structure, {})
        did_something = True

    if args.create_ver:
        structure = read_structure_from_file(dk_hier_file_path, None, prj_name)
        list_existing_dirs_for_categories(base_path, prj_name, categories)
        print("\nExisting $db_ver directories in 'imported' directory:")
        try:
            tree_path = os.path.join(prj_name, 'dbs', 'imported')
            subprocess.run(['tree', '-d', tree_path, '-L', '2'], check=True)
        except FileNotFoundError:
            print("The 'tree' command is not found. Please install it or ensure it's in the PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error displaying directory tree: {e.stderr.decode().strip()}")
        depth_level = detect_db_ver_depth(structure)
        custom_db_vers = display_existing_db_ver_dirs(base_path, structure, depth_level, prj_name, args.create_ver)
        create_directory_structure(base_path, structure, custom_db_vers)
        did_something = True

    if args.init_git:
        git_base_path = os.path.join(base_path, prj_name, 'dbs')
        print(f"Initializing Git repository in: {git_base_path}")
        if os.path.exists(os.path.join(git_base_path, '.git')):
            print(f"Git repository already exists in {git_base_path}. Skipping initialization.")
        else:
            initialize_git_repo(git_base_path)
        configure_git_identity(git_base_path)
        branch_name = args.link_ver or "casino_branch"
        try:
            subprocess.run(['git', 'checkout', '-b', branch_name],
                           cwd=git_base_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['git', 'add', '.'],
                           cwd=git_base_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['git', 'commit', '-m', f'Add directory structure for {branch_name}'],
                           cwd=git_base_path, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['git', 'status'], cwd=git_base_path, check=True)
            print(f"Git operations completed successfully in {git_base_path}.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing Git commands: {e.stderr.decode().strip()}")
        did_something = True

    if not did_something:
        print("At least one option must be provided: -create_ver, (-link_set with -link_ver), or -init_git")
        parser.print_help()
        exit(0)


if __name__ == "__main__":
    main()
