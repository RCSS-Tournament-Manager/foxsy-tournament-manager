import os
import zipfile
import psutil
import re


class Tools:
    @staticmethod
    def  zip_directory(directory_path, zip_file_path):
        # Create a ZipFile object in write mode
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the directory
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    # Create the full file path
                    full_path = os.path.join(root, file)
                    # Add file to the zip file, preserving the directory structure
                    zipf.write(full_path, os.path.relpath(full_path, directory_path))

    @staticmethod
    def unzip_file(zip_file_path, directory_path):
        # Create a ZipFile object in read mode
        with zipfile.ZipFile(zip_file_path, 'r') as zipf:
            # Extract all the contents of zip file in the current directory
            zipf.extractall(directory_path)

    @staticmethod
    def kill_process_tree(pid):
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

    @staticmethod

    def remove_dir(directory_path):
        try:
            os.rmdir(directory_path)
        except OSError as e:
            print(f"Error: {e.strerror}")

    @staticmethod
    def set_permissions_recursive(target_path, mode):
        for root, dirs, files in os.walk(target_path):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), mode)
            for file in files:
                os.chmod(os.path.join(root, file), mode)
        os.chmod(target_path, mode)

    @staticmethod
    def count_matching_lines(lines, pattern):
        regex = re.compile(pattern)

        count = 0
        for line in lines:
            if regex.search(line):
                count += 1

        return count

    @staticmethod
    def find_game_result_from_rcg_file_name(file_name):
        # 20240629155021-team1_0-vs-team2_1.rcg
        # count _ in file_name
        count_ = file_name.count('_')
        left_score = 0
        right_score = 0
        left_penalty = 0
        right_penalty = 0
        if count_ == 2:
            file_name = file_name[:-4]
            first_dash_index = file_name.find('-')
            file_name = file_name[first_dash_index + 1:]
            vs_index = file_name.find('-vs-')
            left_part = file_name[:vs_index]
            last_left_ = left_part.rfind('_')
            left_score = left_part[last_left_ + 1:]
            right_part = file_name[vs_index + 4:]
            last_right_ = right_part.rfind('_')
            right_score = right_part[last_right_ + 1:]
        elif count_ == 4:
            file_name = file_name[:-4]
            first_dash_index = file_name.find('-')
            file_name = file_name[first_dash_index + 1:]
            vs_index = file_name.find('-vs-')
            left_part = file_name[:vs_index]
            first_ = left_part.find('_')
            left_scores = left_part[first_ + 1:]
            first_ = left_scores.find('_')
            left_score = left_scores[:first_]
            left_penalty = left_scores[first_ + 1:]
            right_part = file_name[vs_index + 4:]
            first_ = right_part.find('_')
            right_scores = right_part[first_ + 1:]
            first_ = right_scores.find('_')
            right_score = right_scores[:first_]
            right_penalty = right_scores[first_ + 1:]
        return int(left_score), int(right_score), int(left_penalty), int(right_penalty)
