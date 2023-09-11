#!/bin/bash



if [ -f "cleaning8.log" ]; then
    rm cleaning8.log
fi

if [ -d "toy_data/processed" ]; then
    rm -r toy_data/processed
fi


DATANAME="toy_data"


python run_dist.py --raw_dir ./toy_data/raw --out_dir ./toy_data/processed/ --dirty_dir ./toy_data/processed \
        --batch_size=1024 \
        --no_str_blacklist \
        --bert_clean \
        --cleantext_clean \
        --de_phone \
        --de_qq \
        --n_p 4 \
        2>&1 | tee -a cleaning8.log