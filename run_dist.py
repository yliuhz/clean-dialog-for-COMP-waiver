import os
import logging
import time
import random
from multiprocessing import Pool
from argparse import ArgumentParser

from src.single_filter import main_filter, add_filter_args
from src.inputters.dataloaders import paths_dataloader, all_paths, get_total_truncs
from src.inputters.data_utils import *

from p_tqdm import p_umap
from functools import partial

import ahocorasick
import pickle as pkl

from tqdm import tqdm

random.seed(42)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # - %(name)s
logger = logging.getLogger(__file__)


def get_filter_set(tool_dir, blacklist_filename, regex=True, ns=None):
    blacklist = {}

    # if os.path.exists(os.path.join(tool_dir, blacklist)):
    if blacklist_filename is not None:
        logger.info(f"Using blacklist file: {blacklist_filename}")
        if os.path.exists(os.path.join(tool_dir, blacklist_filename)):
            black_str_set = load_txt(os.path.join(tool_dir, blacklist_filename))[:ns] # 自定义黑名单文件
            blacklist["str_blacklist"] = set(black_str_set)
    else:
        logger.info(f"Using blacklist file: black_str_vocab.txt")
        black_str_set = set(load_txt(os.path.join(tool_dir, "black_str_vocab.txt")))
        blacklist["str_blacklist"] = black_str_set
    


    if regex:
        logger.info("Building regex for blacklist strs")
        blacklist["str_blacklist"] = "|".join(blacklist["str_blacklist"])
    

    if os.path.exists(os.path.join(tool_dir, "black_list_vocab.txt")):
        black_list_set = set(load_txt(os.path.join(tool_dir, "black_list_vocab.txt")))
        blacklist["word_blacklist"] = black_list_set

    if os.path.exists(os.path.join(tool_dir, "special_topic.txt")):
        special_topic_str_set = set(load_txt(os.path.join(tool_dir, "special_topic.txt")))
        blacklist["special_topic"] = special_topic_str_set

    if os.path.exists(os.path.join(tool_dir, "person_name.txt")):
        person_name_set = set(load_txt(os.path.join(tool_dir, "person_name.txt")))
        blacklist["name"] = person_name_set

    en_set = {'l', '.', 'W', 't', 'o', 'z', 'k', 'C', 'B', 'y', '/', 'w', 'a', 's', 'h', 'x', '_', 'n', 'g', 'i',
              'd', 'e'}
    blacklist["english"] = en_set

    confuse_set = set()
    blacklist["confuse"] = confuse_set

    return blacklist


def main():
    parser = ArgumentParser()
    parser.add_argument("--n_p", type=int, default=32, help="Number of subprocess")
    parser.add_argument("--batch_size", type=int, default=500000)
    parser.add_argument("--tool_dir", type=str, default="./tool_data/",
                        help="Path of the tool data.")

    parser.add_argument("--out_dir", type=str, default="./data/", help="Main data dir.")
    parser.add_argument("--dirty_dir", type=str, default="", help="Dir to save dirty cases.")
    parser.add_argument("--raw_dir", type=str, default="./data/raw/", help="Dir of the raw dataset.")

    parser.add_argument("--specified_dataname", type=str, default=None, help="To specify which data to clean")

    parser.add_argument("--blacklist", type=str, default=None, help="filename of tool_data/black_str_vocab.txt")
    parser.add_argument("--regex", action="store_true", help="To use regex to match blacklist strs")

    parser.add_argument("--ns", type=int, default=None, help="Num of sensitive words")
    add_filter_args(parser)
    args = parser.parse_args()
    logger.info(args)

    logger.info("Preparing")
    dataloader = paths_dataloader(args.raw_dir, args.out_dir, args.batch_size, args.specified_dataname)
    NUMOFTRUNCS=get_total_truncs(args.raw_dir, args.out_dir, args.batch_size, args.specified_dataname)
    logger.info(f"Totally {NUMOFTRUNCS} truncs")
    blacklists = get_filter_set(args.tool_dir, args.blacklist, args.regex, args.ns)

    ac = None
    if args.no_str_blacklist:
        if args.ns is not None:
            with open(f"tool_data/__pickled__/ac_{args.ns:d}.pkl", "rb") as f:
                ac = pkl.load(f)
            logger.info(f"Using AC: ac_{args.ns:d}.pkl")
        else:
            with open(f"tool_data/__pickled__/ac_FULL.pkl", "rb") as f:
                ac = pkl.load(f)
            logger.info(f"Using AC: ac_FULL.pkl")
        logger.info(f"Using {len(ac)} blocked words")

    # # single process debug
    # with open("tool_data/__pickled__/ac.pkl", "rb") as f:
    #     ac = pkl.load(f)
    # dataloader = list(dataloader) # next(dataloader)
    # file_id, path, start, end, outpath = dataloader[0]
    # print(f"{path}, {start}, {end}")
    # data = (path, start, end)
    # main_filter(args, file_id, data, blacklists, outpath, args.dirty_dir, ac=ac)
    # exit()

    # multi processing
    p = Pool(args.n_p)
    st = time.time()
    logger.info("Cleaning start!")
    
    for trunc_id, (file_id, path, start, end, outpath) in enumerate(dataloader):
        data = (path, start, end)
        # p.apply_async(main_filter, args=(args, file_id, data, blacklists, outpath, args.dirty_dir, ac, True, args.regex))
        p.apply_async(partial(main_filter, opt=args, blacklist=blacklists, dirty_dir=args.dirty_dir, ac=ac, cut=True, regex=args.regex), args=(file_id, data, outpath, trunc_id, NUMOFTRUNCS))
        # time.sleep(0.01)
    # time.sleep(0.01)
    p.close()
    p.join()
    ed = time.time()
    print(f"END: Total time= {ed-st:.2f}s")
    

    # file_ids, paths, starts, ends, outpaths = all_paths(args.raw_dir, args.out_dir, args.batch_size, args.specified_dataname)
    # n_p = len(file_ids)
    # print(f"n_p={n_p}")
    # p_umap(partial(main_filter, opt=args, blacklist=blacklists, dirty_dir=args.dirty_dir, ac=ac, cut=True, regex=args.regex), file_ids, list(zip(paths,starts,ends)), outpaths, num_cpus=160)


    logger.info("Cleaning over!")
    return


if __name__ == '__main__':
    main()
