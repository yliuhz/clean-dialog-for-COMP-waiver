import os
import gc
import jieba
import tqdm
import collections
import logging

from cleantext import clean

from src.inputters.data_utils import *
from src.rules import session_level, data_level, str_level
import difflib

import traceback

import time

logger = logging.getLogger(__file__)

MAX_LEN_STR_BLACKWORD = 120
SHOWALL = ["zhihu"]
BRACKET = ["weibo_tang"]
SPECIAL_LISTS = ["<EMAIL>", "<PHONE>"]


def str_difference(before, after):
    msg = ""

    a, b = before, after
    # for i,s in enumerate(difflib.ndiff(a, b)):
    #     if s[0]==' ': continue
    #     elif s[0]=='-':
    #         # print(u'Delete "{}" from position {}\n'.format(s[-1],i))
    #         msg += u'Delete "{}" from position {}\n'.format(s[-1],i)
    #     elif s[0]=='+':
    #         # print(u'Add "{}" to position {}\n'.format(s[-1],i)) 
    #         msg += u'Add "{}" to position {}\n'.format(s[-1],i)
    #     if i >= 100:
    #         break

    # dff = difflib.ndiff(a,b)
    # msg += f"{str(list(dff)):s}"

    msg += "\n"
    return msg

def add_dirty_data_log(category1, category2, dirty_data, orig_utter, utterance_new, msg):
    # dirty_data["other"]["cleantext"].add(orig_utter+"\n --> \n"+utterance_new+"\n"+msg)
    dirty_data[category1][category2].add(orig_utter+"\n --> \n"+utterance_new+"\n"+msg)


# def main_filter(opt, file_id, data, blacklist, out_path, dirty_dir, ac=None, cut=True, regex=False): #aynsc
def main_filter(file_id, data, out_path, trunc_id, TOTAL, opt, blacklist, dirty_dir, ac=None, cut=True, regex=False): #aynsc
# def main_filter(file_id, data, out_path, opt, blacklist, dirty_dir, ac=None, cut=True, regex=False): #p_tqdm
# def main_filter(opt):
    try:
        # logger.info("The saved path of data is {}".format(out_path))

        if not os.path.exists(os.path.dirname(out_path)):
            logger.error("{} dost not exist!!!!!!".format(os.path.dirname(out_path)))
            return

        logger.info("Start : {}".format(file_id))
        # data = loader(path)

        dirty_data = {k: collections.defaultdict(set) for k in
                      ["other", "name", "str_blacklist", "word_blacklist", "not_en", "confused", "generic", "emoji",
                       "duplicated", "confuse"]} if dirty_dir else None

        time_dict = collections.defaultdict(float)

        global MAX_LEN_STR_BLACKWORD
        MAX_LEN_STR_BLACKWORD = max(len(x) for x in blacklist["str_blacklist"]) + 2

        res = []
        if isinstance(data, tuple):
            if data[0].endswith(".jsonl"):
                data = load_lines(data[0], data[1], data[2])
            elif data[0].endswith(".json"):
                data = load_json_data(data[0], data[1], data[2])
            else:
                raise NotImplementedError

        # logger.info("Size of this batch : {}, log in {}".format(len(data), file_id))
        # # logger.info("Batch sample: {}, log in {}".format(data[0][0], file_id))
        # print(f"Len(data)={len(data)}, {type(data)}")
        # print(data.pop(0))
        # print(f"Len(data)={len(data)}, {type(data)}")


        d_idx = 0
        while len(data):
            d_idx += 1

            dialog = data.pop(0)
            # session level
            # dialog = session_check(opt, dialog)
            if opt.no_utter_dup:
                if len(set(dialog)) < 2:
                    if dirty_data and len(set(dialog)) > 0:
                        dirty_data["other"]["less_pair"].add(dialog[0])
                    continue
            

            new_dialog = []
            for i in range(len(dialog)):
                if opt.split_multi_repost:
                    utters = str_level.split_multi_repost(dialog[i])
                else:
                    utters = [dialog[i]]

                skip_utter = False
                for j, utter in enumerate(utters):
                    if skip_utter:
                        skip_utter = False
                        continue
                    if opt.no_toupiao and (j + 1) < len(utters):
                        toupiao = str_level.no_toupiao(utters[j + 1])
                        if toupiao:
                            skip_utter = True
                            if dirty_data:
                                dirty_data["other"]["toupiao"].add(utters[j] + "\t\t" + utters[j + 1])
                            continue
                    

                    tight_utter = utter.replace(" ", "")

                    utter = utterance_clean(opt, file_id, utter, tight_utter, blacklist, dirty_data, time_dict, cut, regex=regex, ac=ac)
                    # print("*"*20)
                    # print(utter[:60])
                    # print("*"*20)
                    new_dialog.append(utter)


            if opt.re_name:
                new_dialog = session_level.de_name(new_dialog, blacklist["name"])

            # print(f"LenofNewdialog= {len(new_dialog)}")
            start_idx = 0 if new_dialog[0] else 1
            for i in range(1, len(new_dialog) + 1):
                if i == len(new_dialog) or not new_dialog[i]:
                    if opt.no_short_response:
                        part_dialog = new_dialog[start_idx: i][:]
                        part_dialog = session_level.no_short_response(part_dialog)
                        # if len(part_dialog) > 1:
                        if len(part_dialog) > 0:
                            res.append(part_dialog)
                    else:
                        # if len(new_dialog[start_idx: i]) > 1: #原代码只保留了对话(有问有答)，这里修改为只要有内容就保存
                        if len(new_dialog[start_idx: i]) > 0:
                            res.append(new_dialog[start_idx: i])
                    start_idx = i + 1
            
            
            # for i in range(1, len(new_dialog)):
            #     if not new_dialog[i]:
            #         if len(new_dialog[start_idx: i]) > 1:
            #             res.append(new_dialog[start_idx: i])
            #         start_idx = i + 1
            #     elif i == len(new_dialog) - 1:
            #         if len(new_dialog[start_idx:]) > 1:
            #             res.append(new_dialog[start_idx:])


            # print(f"ST2={eed2-sst2:.2f}, {eed3-eed2:.2f} {eeed1-ssst1:.2f} {eeed2-eeed1:.2f} {d_idx}/{len(data)} {len(dialog)} {dialog[0][:10]}")

        # data level
        if opt.no_ad:
            res = data_level.no_ad(res, dirty_data)

        if opt.de_generic_dialog:
            res = data_level.de_generic(res, dirty_data, out_path.replace(".jsonl", "_trigram.jsonl"), 1000)

        # print(f"lenofres: {len(res)}")
        if len(res) > 0:
            # save_jsonl(res, out_path)
            save_txt("\n".join(["\t\t".join(x) for x in res]), out_path)
            # logger.info("Resulting {} dialogs".format(len(res)))
            del res, data
            gc.collect()

        # save dirty data
        if dirty_dir:
            save_dirty(dirty_dir, dirty_data, file_id)
        logger.info("{}  over [{}/{}]".format(file_id, trunc_id+1, TOTAL))



        # print(f"T1={ed1-st:.2f}s, T2={ed2-ed1:.2f}s, T3={ed3-ed2:.2f}s")
        # print(f"ST1={eed1-sst1:.2f}s")
    except Exception as e:
        logger.error("Error !!!! : {}:{}, {}".format(e.__class__.__name__, e, traceback.format_exc()))
    return file_id


def save_dirty(dirty_dir, dirty_data, file_id):
    dirty_dir = os.path.join(dirty_dir, "dirty_data")
    if not os.path.isdir(dirty_dir):
        os.makedirs(dirty_dir, exist_ok=True)
    for k, v in dirty_data.items():
        k_path = os.path.join(dirty_dir, k)
        if sum(len(subv) for subv in v.values()):
            if not os.path.isdir(k_path):
                os.mkdir(k_path)
            if "blacklist" in k and len(v) > 0:
                temp_bl = {bk: len(bv) for bk, bv in v.items()}
                temp_bl = sorted(temp_bl.items(), key=lambda x: x[1], reverse=True)
                save_json(temp_bl, os.path.join(k_path, "sta_{}.json".format(file_id)))
                save_json({bk: list(bv) for bk, bv in v.items()}, os.path.join(k_path, "{}.json".format(file_id)))
            else:
                for sub_k, sub_v in v.items():
                    if len(sub_v) > 0:
                        # save_jsonl(sub_v, os.path.join(k_path, "{}_{}.jsonl".format(sub_k, file_id)))
                        save_txt(sub_v, os.path.join(k_path, "{}_{}.txt".format(sub_k, file_id)))
    del dirty_data
    gc.collect()
    return


def add_filter_args(argparser):
    opt = argparser.add_argument_group('Filter Arguments')

    opt.add_argument('--no_utter_dup', action="store_true")
    opt.add_argument('--re_name', action="store_true")
    opt.add_argument('--split_multi_repost', action="store_true")
    opt.add_argument('--no_ad', action="store_true")
    opt.add_argument('--de_generic_dialog', action="store_true")
    opt.add_argument('--de_reply_tag', action="store_true")
    opt.add_argument('--de_hashtag', action="store_true")
    opt.add_argument('--de_emotion', action="store_true")
    opt.add_argument('--de_mention', action="store_true")
    opt.add_argument('--de_repost', action="store_true")
    opt.add_argument('--de_duplicated', action="store_true")
    opt.add_argument('--de_emoji', action="store_true")
    opt.add_argument('--no_short', action="store_true")
    opt.add_argument('--no_long', action="store_true")
    opt.add_argument('--no_special_topic', action="store_true")
    opt.add_argument('--bert_clean', action="store_true")
    opt.add_argument('--cleantext_clean', action="store_true")
    opt.add_argument('--no_str_blacklist', action="store_true")
    opt.add_argument('--no_toupiao', action="store_true")
    opt.add_argument('--no_short_response', action="store_true")
    opt.add_argument('--no_specific_utter', action="store_true")
    opt.add_argument('--contain_zh', action="store_true")
    opt.add_argument('--de_single_repost_mention', action="store_true")
    opt.add_argument('--de_weibo_url', action="store_true")
    opt.add_argument('--de_url', action="store_true")
    opt.add_argument('--no_mention', action="store_true")
    opt.add_argument('--de_angle', action="store_true")
    opt.add_argument('--de_alpha_num', action="store_true")
    opt.add_argument('--de_phone', action="store_true")
    opt.add_argument('--de_qq', action="store_true")
    opt.add_argument('--de_specific', action="store_true")

    # Yue LIU
    opt.add_argument('--de_html', action="store_true")

    # special files
    opt.add_argument('--de_showall', action="store_true")
    opt.add_argument('--de_brackets', action="store_true")

    # words list level
    opt.add_argument('--no_word_blacklist', action="store_true")
    opt.add_argument('--no_alpha_noise', action="store_true")
    opt.add_argument('--check_confuse_word', action="store_true")
    opt.add_argument('--yda_dedupl', action="store_true")
    # todo remedy http


def utterance_clean(opt, file_id, utterance, tight_utter, blacklist, dirty_data, time_dict, cut,
                    return_segmented=True, regex=True, ac=None) -> str:

    orig_utter = utterance[:]
    utterance = utterance.strip()

    

    utterance = utterance.replace("alink", "")

    # TODO check
    if "¡ 评论" in utterance:
        utterance = utterance[:utterance.index("¡ 评论")]
        if dirty_data:
            dirty_data["other"]["¡ 评论"].add(orig_utter)


    if utterance and opt.no_specific_utter:
        specific_utter = str_level.no_specific_utter(tight_utter)
        if specific_utter:
            if dirty_data:
                dirty_data["other"]["specific_utter"].add(orig_utter)
            utterance = ""

    if utterance and opt.de_reply_tag:
        len_before = len(utterance)
        utterance = str_level.REPLY_MENTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_reply_tag"].add(orig_utter)

    # regex
    if utterance and opt.de_angle:
        len_before = len(utterance)
        utterance = str_level.ANGLE_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["angle"].add(orig_utter)

    if utterance and opt.de_url:
        len_before = len(utterance)
        utterance = str_level.URL_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["url"].add(orig_utter)

    if utterance and opt.de_weibo_url:
        len_before = len(utterance)
        utterance = str_level.WEIBO_URL_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["weibo_url"].add(orig_utter)

    if utterance and opt.de_brackets:
        len_before = len(utterance)
        utterance = str_level.BRACKETS_REGEX2.sub("", utterance).strip()
        # utterance = str_level.BRACKETS_REGEX3.sub("", utterance).strip()
        if any([x for x in BRACKET if x in file_id]):
            utterance = str_level.BRACKETS_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["weibo_emoji"].add(orig_utter)

    if utterance and opt.de_hashtag:
        len_before = len(utterance)
        utterance = str_level.HASHTAG_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["hashtag"].add(orig_utter)

    if utterance and opt.de_emotion:
        len_before = len(utterance)
        utterance = str_level.EMOTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["emotion"].add(orig_utter)

    if utterance and opt.de_html:
        len_before = len(utterance)
        utterance_new = str_level.HTML_REGEX.sub("", utterance).strip()
        msg = str_difference(utterance, utterance_new)
        if dirty_data and len(utterance_new) < len_before:
            # dirty_data["emoji"]["html"].add(orig_utter)
            add_dirty_data_log("emoji", "html", dirty_data, utterance, utterance_new, msg)
        utterance = utterance_new

    if utterance and opt.no_mention:
        if str_level.contain_at(utterance):
            if dirty_data:
                dirty_data["other"]["mention"].add(orig_utter)
            utterance = ""

    if utterance and opt.de_mention:
        len_before = len(utterance)
        # utterance = str_level.COMMON_MENTION_REGEX.sub("", utterance).strip()
        utterance = str_level.no_at(utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["no_at"].add(orig_utter)

    if utterance and opt.de_single_repost_mention:
        len_before = len(utterance)
        utterance = str_level.SINGLE_REPPOST_MENTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["single_repost"].add(orig_utter)

    if utterance and opt.de_repost:
        len_before = len(utterance)
        utterance = str_level.REPPOST_MENTION_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["repost_mention"].add(orig_utter)

    if utterance and opt.de_showall and any([x for x in SHOWALL if x in file_id]):
        len_before = len(utterance)
        utterance = str_level.ZHIHU_SHOW_ALL_REGEX.sub("", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["showall"].add(orig_utter)

    if utterance and opt.de_emoji:
        len_before = len(utterance)
        utterance, emo = str_level.remove_emoji3(utterance)
        if dirty_data and len(utterance) < len_before:
            dirty_data["emoji"]["emoji"].add(emo[0]+": "+orig_utter)

    if utterance and opt.de_alpha_num:
        len_before = len(utterance)
        utterance = str_level.ALPHA_NUM_REGEX.sub(" ", utterance).strip()
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_alpha_num"].add(orig_utter)

    if utterance and opt.de_specific:
        len_before = len(utterance)
        utterance = str_level.de_specific(utterance)
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_specific"].add(orig_utter)


    if utterance and opt.de_phone:
        len_before = len(utterance)
        utterance_new = str_level.PHONE_REGEX.sub("</PHONE>", utterance).strip()
        msg = str_difference(utterance, utterance_new)
        if dirty_data and len(utterance_new) < len_before:
            # dirty_data["other"]["de_phone"].add(orig_utter)
            add_dirty_data_log("other", "de_phone", dirty_data, utterance, utterance_new, msg)
        utterance = utterance_new



    if utterance and opt.de_qq:
        len_before = len(utterance)
        utterance_new = str_level.QQ_REGEX.sub(" ", utterance).strip()
        msg = str_difference(utterance, utterance_new)
        if dirty_data and len(utterance_new) < len_before:
            # dirty_data["other"]["de_qq"].add(orig_utter)
            add_dirty_data_log("other", "de_qq", dirty_data, utterance, utterance_new, msg)
        utterance = utterance_new


    # clean-text lib

    if utterance and opt.cleantext_clean:
        len_before = len(utterance)
        utterance_new = clean(
            utterance,
            fix_unicode=True,
            to_ascii=False,
            lower=False,
            normalize_whitespace=True,
            no_line_breaks=True,
            no_urls=False,
            no_emails=True,
            no_phone_numbers=True,
            replace_with_url=" ",
            replace_with_email="</EMAIL>",
            replace_with_phone_number="</PHONE>",
        )
        msg = str_difference(utterance, utterance_new)
        if dirty_data and len(utterance_new) < len_before:
            # dirty_data["other"]["cleantext"].add(orig_utter+"\n --> \n"+utterance_new+"\n"+msg)
            add_dirty_data_log("other", "cleantext", dirty_data, utterance, utterance_new, msg)
        utterance = utterance_new



    if utterance and opt.bert_clean:
        utterance_new = str_level.bert_clean(utterance)
        msg = str_difference(utterance, utterance_new)
        if len(utterance_new) < len(utterance):
            add_dirty_data_log("other", "bert_clean", dirty_data, utterance, utterance_new, msg)
        utterance = utterance_new

    # print("*"*20)
    # print(utterance[:60])
    # print("*"*20)

    if utterance and opt.de_emoji:
        utterance = str_level.COLON_REGEX.sub("", utterance).strip()

    if utterance and opt.contain_zh:
        if not str_level.contains_Chinese(utterance):
            if dirty_data:
                dirty_data["other"]["contain_zh"].add(orig_utter)
            utterance = ""

    if utterance and opt.no_special_topic:
        special_topic_word = str_level.de_str_blacklist(tight_utter, blacklist["special_topic"])
        if special_topic_word:
            if dirty_data:
                dirty_data["special_topic"][special_topic_word].add(orig_utter)
            utterance = ""

    # print("*"*20)
    # print(utterance[:60])
    # print("*"*20)

    if utterance and opt.no_str_blacklist:
        utterance = str_level.TM_REGEX.sub(lambda m: m.group(1) + m.group(3), utterance) #去除句子中的tm骂人话

        # print("*"*20)
        # print(utterance[:60])
        # print("*"*20)
        global MAX_LEN_STR_BLACKWORD
        # if not regex:
        #     black_word = str_level.de_str_blacklist2(tight_utter, blacklist["str_blacklist"], MAX_LEN_STR_BLACKWORD)
        # else:
        #     black_word = str_level.de_str_blacklist3(tight_utter, blacklist["str_blacklist"]) # 使用正则表达式匹配敏感词
        black_word, utterance_new = str_level.de_str_blacklist4(utterance, blacklist["str_blacklist"], ac=ac)
        if black_word:
            if dirty_data:
                dirty_data["str_blacklist"][black_word].add(orig_utter)
            # utterance = ""
            utterance = utterance_new

    # print("*"*20)
    # print(utterance[:60])
    # print("*"*20)

    if utterance and opt.de_duplicated:
        len_before = len(utterance)
        utterance = str_level.reduce_duplicated_phrase(utterance)
        if dirty_data and len(utterance) < len_before:
            dirty_data["other"]["de_duplicated"].add(orig_utter)

    if utterance and opt.no_short:
        len_flag = str_level.too_short(utterance)
        if len_flag:
            if dirty_data:
                dirty_data["other"]["short"].add(orig_utter)
            utterance = ""

    if utterance and opt.no_long:
        len_flag = str_level.too_long(utterance)
        if len_flag:
            if dirty_data:
                dirty_data["other"]["long"].add(orig_utter)
            utterance = ""


    if not any([opt.no_alpha_noise, opt.check_confuse_word, opt.no_word_blacklist, opt.yda_dedupl]):
        

        ret =  utterance.strip()
        # print("*"*20)
        # print(ret[:60])
        # print("*"*20)


        # print(f"{ed1-st1:.2f} {ed2-st2:.2f} {ed3-st3:.2f} {ed4-st4:.2f} {ed5-st5:.2f} {ed6-st6:.2f} {ed7-st7:.2f} {ed8-st8:.2f} {orig_utter[:10]:s}")

        return ret

    ### word level
    if cut:
        word_list = list(jieba.cut(utterance))
    else:
        word_list = utterance.strip().split()

    if word_list and opt.no_alpha_noise:
        alpha_word = str_level.not_en(word_list, blacklist["english"])
        if alpha_word:
            if dirty_data:
                dirty_data["not_en"][alpha_word].add(orig_utter)
            word_list = []
            utterance = ""

    if word_list and opt.check_confuse_word:
        confuse_word = str_level.check_confuse(word_list, blacklist["confuse"])
        if confuse_word:
            if dirty_data:
                dirty_data["confuse"][confuse_word].add(orig_utter)

    if word_list and opt.no_word_blacklist:
        dirty_word = str_level.de_word_blacklist(word_list, blacklist["word_blacklist"])
        if dirty_word:
            if dirty_data:
                dirty_data["word_blacklist"][dirty_word].add(orig_utter)
            word_list = []
            utterance = ""

    if word_list and opt.yda_dedupl:
        yda_dupl_flag = str_level.judge_yda_dupl(word_list)
        if yda_dupl_flag:
            if dirty_data:
                dirty_data["duplicated"]["yda"].add(orig_utter)
            word_list = []
            utterance = ""

    # print(f"{ed1-st1:.2f} {ed2-st2:.2f} {ed3-st3:.2f} {ed4-st4:.2f} {ed5-st5:.2f} {orig_utter[:10]:s}")
    return " ".join(word_list).strip() if return_segmented else utterance.strip()
