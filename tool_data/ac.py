
import ahocorasick
import pickle as pkl
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", default=None, type=int)
    args = parser.parse_args()

    ac = ahocorasick.Automaton()

    filename = "blacklist_str_re_merge.txt"

    with open(filename, "r") as f:
        lines = f.readlines()
        lines = [x.strip() for x in lines]

        if args.n:
            n = min(args.n, len(lines))
            lines = lines[:n]
        else:
            n = "FULL"

    for i, word in enumerate(lines):
        ac.add_word(word, (i, word))

    ac.make_automaton()

    os.makedirs("__pickled__", exist_ok=True)
    with open(f"__pickled__/ac_{n}.pkl", "wb") as fout:
        pkl.dump(ac, fout)

        print(f"Output to __pickled__/ac_{n}.pkl")


    # with open("__pickled__/ac.pkl", "rb") as f:
    #     ac2 = pkl.load(f)

    string = "🐯 200305 官咖更新 顺荣相关 宝贝又半夜不睡觉了🎂[2020生日企划-2]: 👔[hoshi衣橱pk]: 📹[毒:fear直拍]: 🗂 [签售整理]:"
    res = ac.iter(string)
    for end_index, (insert_order, original_value) in res:
        start_index = end_index - len(original_value) + 1
        print((start_index, end_index, (insert_order, original_value)))
        assert string[start_index:start_index + len(original_value)] == original_value
    
