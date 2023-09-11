import os
import random
import platform
from src.inputters.data_utils import *
from math import ceil

import logging
logger = logging.getLogger(__file__)

def simple_dataloader(dir_path, out_dir, batch_size):
    """Load jsonl data, each line should be a list of dialog: ["你好", "你也好", "哈哈"]"""
    cleaned_dir = os.path.join(out_dir, "cleaned_data")
    if not os.path.exists(cleaned_dir):
        os.mkdir(cleaned_dir)

    subdirs = [(subdir, os.path.join(dir_path, subdir)) for subdir in os.listdir(dir_path)]
    jsonl_path_list = [(file, subdir, os.path.join(subdir_path, file))
                       for subdir, subdir_path in subdirs
                       for file in os.listdir(subdir_path) if file.endswith(".jsonl")]
    # random.shuffle(jsonl_path_list)
    for file, subdir_name, path in jsonl_path_list:
        dataset = load_jsonl(path)
        for i in range(0, len(dataset), batch_size):
            fid = subdir_name + "_" + file.replace(".jsonl", "") + "_trunc" + str(i)
            # out
            out_subdir = os.path.join(cleaned_dir, subdir_name)
            if not os.path.exists(out_subdir):
                os.mkdir(out_subdir)
            out_path = os.path.join(out_subdir, fid + ".jsonl")
            yield fid, dataset[i: i + batch_size], out_path


def paths_dataloader(dir_path, out_dir, batch_size, specified_dataname=None):
    """Load jsonl data, each line should be a list of dialog: ["你好", "你也好", "哈哈"]"""
    cleaned_dir = os.path.join(out_dir, "cleaned_data")
    if not os.path.exists(cleaned_dir):
        os.makedirs(cleaned_dir)

    # subdirs = [(subdir, os.path.join(dir_path, subdir)) for subdir in os.listdir(dir_path)]

    subdirs = []
    for subdir in os.listdir(dir_path):
        fullpath = os.path.join(dir_path, subdir)
        if os.path.isdir(fullpath):
            if specified_dataname is None:
                # Find and clean all the data
                subdirs.append((subdir, fullpath))
            else:
                # Only clean the specified data
                if subdir == specified_dataname:
                    subdirs.append((subdir, fullpath))
                    break



    jsonl_path_list = [(file, subdir, os.path.join(subdir_path, file))
                       for subdir, subdir_path in subdirs
                       for file in os.listdir(subdir_path) if file.endswith(".jsonl") or file.endswith(".json")]
    
    if len(jsonl_path_list) > 0:
        logger.info(f"Totally {len(jsonl_path_list)} files to clean: {list(zip(*jsonl_path_list))[0]}")

    # random.shuffle(jsonl_path_list)
    for file, subdir_name, path in jsonl_path_list:
        # dataset = load_jsonl(path)
        if platform.system() == "Windows":
            file_len = buff_count(path)
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            file_len = wc_count(path)
            logger.info(f"{file} {subdir_name} total+lines= {file_len}")
        else:
            raise Exception
        for i in range(0, file_len, batch_size):
            fid = subdir_name + "_" + file.replace(".jsonl", "") + "_trunc" + str(i)
            # out
            out_subdir = os.path.join(cleaned_dir, subdir_name)
            if not os.path.exists(out_subdir):
                os.mkdir(out_subdir)
            out_path = os.path.join(out_subdir, fid + ".txt")
            yield fid, path, i, i + batch_size, out_path

def get_total_truncs(dir_path, out_dir, batch_size, specified_dataname=None):
    # subdirs = [(subdir, os.path.join(dir_path, subdir)) for subdir in os.listdir(dir_path)]

    subdirs = []
    for subdir in os.listdir(dir_path):
        fullpath = os.path.join(dir_path, subdir)
        if os.path.isdir(fullpath):
            if specified_dataname is None:
                # Find and clean all the data
                subdirs.append((subdir, fullpath))
            else:
                # Only clean the specified data
                if subdir == specified_dataname:
                    subdirs.append((subdir, fullpath))
                    break



    jsonl_path_list = [(file, subdir, os.path.join(subdir_path, file))
                       for subdir, subdir_path in subdirs
                       for file in os.listdir(subdir_path) if file.endswith(".jsonl") or file.endswith(".json")]

    # random.shuffle(jsonl_path_list)
    ret = 0
    for file, subdir_name, path in jsonl_path_list:
        # dataset = load_jsonl(path)
        if platform.system() == "Windows":
            file_len = buff_count(path)
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            file_len = wc_count(path)
        else:
            raise Exception
        ret += ceil(file_len / batch_size)

    return ret


def all_paths(dir_path, out_dir, batch_size, specified_dataname=None):
    """Load jsonl data, each line should be a list of dialog: ["你好", "你也好", "哈哈"]"""
    cleaned_dir = os.path.join(out_dir, "cleaned_data")
    if not os.path.exists(cleaned_dir):
        os.makedirs(cleaned_dir)

    # subdirs = [(subdir, os.path.join(dir_path, subdir)) for subdir in os.listdir(dir_path)]

    subdirs = []
    for subdir in os.listdir(dir_path):
        fullpath = os.path.join(dir_path, subdir)
        if os.path.isdir(fullpath):
            if specified_dataname is None:
                # Find and clean all the data
                subdirs.append((subdir, fullpath))
            else:
                # Only clean the specified data
                if subdir == specified_dataname:
                    subdirs.append((subdir, fullpath))
                    break



    jsonl_path_list = [(file, subdir, os.path.join(subdir_path, file))
                       for subdir, subdir_path in subdirs
                       for file in os.listdir(subdir_path) if file.endswith(".jsonl")]
    # random.shuffle(jsonl_path_list)
    file_ids, paths, starts, ends, outpaths = [], [], [], [], []
    for file, subdir_name, path in jsonl_path_list:
        # dataset = load_jsonl(path)
        if platform.system() == "Windows":
            file_len = buff_count(path)
        elif platform.system() == "Linux":
            file_len = wc_count(path)
        else:
            raise Exception
        for i in range(0, file_len, batch_size):
            fid = subdir_name + "_" + file.replace(".jsonl", "") + "_trunc" + str(i)
            # out
            out_subdir = os.path.join(cleaned_dir, subdir_name)
            if not os.path.exists(out_subdir):
                os.mkdir(out_subdir)
            out_path = os.path.join(out_subdir, fid + ".txt")
            # yield fid, path, i, i + batch_size, out_path
            file_ids.append(fid)
            paths.append(path)
            starts.append(i)
            ends.append(i+batch_size)
            outpaths.append(out_path)

    return file_ids, paths, starts, ends, outpaths