'''
https://huggingface.co/thu-coai/roberta-base-cold
https://doi.org/10.48550/arXiv.2201.06025
'''



import torch
from transformers.models.bert import BertTokenizer, BertForSequenceClassification
import numpy as np



if __name__ == "__main__":

    tokenizer = BertTokenizer.from_pretrained('thu-coai/roberta-base-cold')
    model = BertForSequenceClassification.from_pretrained('thu-coai/roberta-base-cold')
    model.eval()

    filename = "../tool_data/black_str_vocab.txt"

    with open(filename, "r") as f:
        # texts = ['你就是个傻逼！','黑人很多都好吃懒做，偷奸耍滑！','男女平等，黑人也很优秀。']

        texts = f.readlines()
        texts = [x.strip() for x in texts]

        print("Tokenizing")
        model_input = tokenizer(texts,return_tensors="pt",padding=True)

        print("Inferring")
        model_output = model(**model_input, return_dict=False)
        prediction = torch.argmax(model_output[0].cpu(), dim=-1)
        prediction = [p.item() for p in prediction]
        # print(prediction) # --> [1, 1, 0] (0 for Non-Offensive, 1 for Offenisve)


        non_off_idx = np.where(prediction == 0)[0]
        non_off_texts = np.array(texts)[non_off_idx]

        print(f"Num of Non-offensive texts= {len(non_off_texts)}")

        print("Writing Results")
        out_filename = "N_" + filename.split("/")[-1]
        with open(out_filename, "w") as fout:
            for text in non_off_texts:
                f.write(f"{text}\n")


