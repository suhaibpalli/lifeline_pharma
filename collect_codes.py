import os

def read_selected_code_files_to_txt(
    root_dir,
    exclude_files=None,
    exclude_folders=None,
    output_file='all_content.txt'
):
    """
    Read all .py, .html, .js, .ts, .tsx, .json, .mjs, .env, .env.local, .yml, .yaml files in root_dir recursively,
    excluding specified files and folders and docker-related files, and write their contents to output_file.
    """
    # Set of file extensions to include (extension must include dot)
    code_extensions = {
        '.py', '.html', '.js', '.ts', '.tsx',
        '.json', '.mjs', '.env', '.production',
        '.yml', '.yaml', '.css'
    }
    # Filenames to include regardless of extension (e.g. .env.local)
    # Dockerfile and docker-compose files are deliberately NOT included
    special_include_filenames = {
        '.env.local'
    }

    # Patterns for docker-related filenames to explicitly exclude
    docker_exclude_names = {
        'dockerfile',
        'docker-compose.yml',
        'docker-compose.yaml'
    }

    exclude_files = exclude_files or []
    exclude_folders = exclude_folders or []

    # Add dockerfile and docker-compose to excluded files (if not present)
    for docker_name in docker_exclude_names:
        if docker_name not in (f.lower() for f in exclude_files):
            exclude_files.append(docker_name)

    # Normalize excluded folder paths to use os.sep for cross-platform compatibility
    exclude_folders_normalized = set(
        os.path.normpath(folder) for folder in exclude_folders
    )

    # Write the output file into the current working directory
    output_path = os.path.join(os.getcwd(), output_file)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for subdir, dirs, files in os.walk(root_dir):
            # Exclude folders (by name and by relative path)
            rel_subdir = os.path.relpath(subdir, root_dir)
            dirs[:] = [
                d for d in dirs
                if d not in exclude_folders_normalized and
                   os.path.normpath(os.path.join(rel_subdir, d)) not in exclude_folders_normalized
            ]
            for file in files:
                # Always exclude dockerfile and docker-compose files (case insensitive)
                file_lower = file.lower()
                if file in exclude_files or file_lower in docker_exclude_names:
                    continue
                _, ext = os.path.splitext(file)
                include_this = False
                if ext.lower() in code_extensions:
                    include_this = True
                elif file in special_include_filenames:
                    include_this = True
                elif file_lower in {name.lower() for name in special_include_filenames}:
                    include_this = True
                # Last check: skip Dockerfile and docker-compose again, even if extension matches
                if file_lower in docker_exclude_names:
                    continue

                if not include_this:
                    continue

                filepath = os.path.join(subdir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(f"\n---{filepath}---\n")
                        outfile.write(content)
                        outfile.write('\n')
                except Exception:
                    # Skip files which can't be read as text (e.g. binaries)
                    pass


if __name__ == '__main__':
    # Define root directory where your files are located
    root_directory = '.'  # change as needed

    # Define list of file names to exclude
    excluded_files = [
        'manage.py', 'LICENSE', 'collect_codes.py', 'all_files_combined.txt', '.pylintrc',
        'CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', 'README.md', 'TODO.md', 
        # Exclude specific template files
        # '400.html', '403.html', '404.html', '500.html', 'error_handler_base.html',
        # 'invoices.html', 'invoice_detail.html', 'privacy.html', 'term.html',
        'package-lock.json', 'tree.py', 'tree_output.txt',
        # Dockerfile and docker compose files should be excluded explicitly for redundancy
        'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        'api.ts'
    ]

    # Define list of folder names to exclude (use forward slashes for cross-platform compatibility)
    excluded_folders = [
        'migrations', '__pycache__', 'static',
        '.github', '.idea', '.vscode', 'lmsa',
        '.next', 'node_modules', 'eerp', 'venv',
        'frontend',
        'academics',
        'videoconferencing',
        "admissions",
        # 'hr',
        # "backend",
        "ai-service",
        "frontend/lib/api/generated",
        "frontend/types/api.d.ts",
        'generated',
        'frontend\types\api.ts',
        'staticfiles'
    ]

    # Call the function to combine files, output file goes into current executing directory
    read_selected_code_files_to_txt(root_directory, excluded_files, excluded_folders, 'all_files_combined.txt')
