# LMFlowDataCleaning

多进程语料清洗框架，基于[clean-dialog](https://github.com/lemon234071/clean-dialog/tree/master)进行优化。

## 优化项目

- [x] 敏感词匹配算法修改为[AC自动机](https://en.wikipedia.org/wiki/Aho%E2%80%93Corasick_algorithm)
- [x] 可选多进程进度条
- [x] 支持更多输入格式 
- [x] 修改清洗策略为替换
- [ ] 支持`word1 + word2`格式的敏感词

## 快速开始

```bash
python -m pip install -r requirements.txt
chmod a+x scripts/*.sh && ./script/run8.sh
```

清洗后的数据在`./toy_data/processed/cleaned_data/`下，脏数据在`./toy_data/processed/dirty_data/`下。

## 数据准备

按照格式准备数据，参照项目中的toy_data目录，

### 数据格式

当前支持`json`格式和`jsonl`格式的输入数据。

#### jsonl

```jsonl
["怎么会有老鼠呢？", "因为我现在住的房子又老又旧,前后都是树子,简直是耗子寄居的绝佳场所."]
["吃完头顶会有原谅色嘛", "啊！这个没看诶但是我觉得没有", "嗯～有机会回理工大去试试", "哈哈哈我朋友做的"]
["阿巴阿巴"]
```

#### json

```json
{
    "type": "text-only",
    "instances": [
        {
            "text": "哇，这么好！！"
        },
        {
            "text": "泪点真滴"
        }
    ]
}
```

1. 一样地给自己的数据建立一个目录，mkdir wait4clean_data
2. 每一个数据集分开一个目录，mkdir wait4clean_data/data_1
3. 按照clean-dialog-new/toy_data/raw/test1/testdata.jsonl的format整理数据，然后把数据放在wait4clean_data/data_1下

## 参数解释

- `--raw_dir`: 输入文件夹
- `--out_dir`和`--dirty_dir`: 输出文件夹
- `--batch_size`: 批处理大小
- `--no_str_blacklist`: 去除敏感词，敏感词文件在`./tool_data/`下
- `--bert_clean`: 去除特殊符号
- `--cleantext_clean`: 匿名化、修复编码问题
- `--de_phone`: 删除电话号码
- `--de_qq`: 删除QQ号码
- `--n_p`: 使用CPU核数
- `--specified_dataname`: 只清洗文件夹内的特定数据


### 自定义敏感词列表

将新的敏感词列表`.txt`放置在`./tool_data`下，执行

```bash
cd ./tool_data && python ac.py
```

生成AC自动机文件。

## 输出格式

清洗后的数据输出为`.txt`格式，同一行的多条对话由`\t\t`分隔

```txt
怎么会有老鼠呢?   因为我现在住的房子又老又旧,前后都是树子,简直是耗子寄居的绝佳场所.
"吃完头顶会有原谅色嘛"    "啊！这个没看诶但是我觉得没有"    "嗯～有机会回理工大去试试"    "哈哈哈我朋友做的"
```

## 相关链接

- [clean-dialog](https://github.com/lemon234071/clean-dialog/tree/master)
- [pyahocorasick](https://pypi.org/project/pyahocorasick)