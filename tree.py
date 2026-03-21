import os

def write_tree_with_exclusions(root_dir, exclude_dirs, output_file):
    """
    Mimics the 'tree /f' Windows command, writing the folder and file structure to a text file,
    but excludes any directories whose (base) name is in the exclude_dirs list.
    """
    def tree(dir_path, prefix='', out_lines=[]):
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        # Filter out excluded directories
        entries = [
            e for e in entries
            if e not in exclude_dirs or not os.path.isdir(os.path.join(dir_path, e))
        ]
        entries_count = len(entries)
        for idx, entry in enumerate(entries):
            full_path = os.path.join(dir_path, entry)
            connector = "└── " if idx == entries_count - 1 else "├── "
            out_lines.append(f"{prefix}{connector}{entry}")
            if os.path.isdir(full_path):
                extension = "    " if idx == entries_count - 1 else "│   "
                tree(full_path, prefix=prefix + extension, out_lines=out_lines)
        return out_lines

    lines = [root_dir]
    lines += tree(root_dir, '')
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(f"{line}\n")

# Example usage:
if __name__ == '__main__':
    # Folder to print tree for
    root_folder = "."  # You may set this to any folder
    # List of folder names to exclude (updated per instruction)
    exclude_list = ["eerp", "node_modules", ".next", ".git", "__pycache__",
    # "backend", "ai-service",
    # "frontend"
    ]
    # Output file name
    output_txt = "tree_output.txt"

    write_tree_with_exclusions(root_folder, exclude_list, output_txt)