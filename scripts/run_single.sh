#!/bin/bash


DATANAME="wiki"


python run_dist.py --raw_dir ./llmdata --out_dir ./llmdata/output5/ --dirty_dir ./llmdata/output5/ \
        --batch_size=10000 \
        --specified_dataname=$DATANAME \
        --split_multi_repost \
        --de_reply_tag \
        --de_hashtag \
        --de_single_repost_mention \
        --de_duplicated \
        --de_emoji \
        --bert_clean \
        --cleantext_clean \
        --no_specific_utter \
        --no_toupiao \
        --de_url \
        --de_weibo_url \
        --contain_zh \
        --no_mention \
        --de_showall \
        --de_brackets \
        --de_specific \
        --de_phone \
        --de_qq \
        --de_alpha_num \
        --n_p 160 \
        2>&1 | tee -a cleaning.log