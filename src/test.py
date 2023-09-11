
import os
import json
import time

def read_lines(f, start, end):
    data = []
    i = -1
    for line in f:
        i += 1
        if i > end - 1:
            break
        if i > start - 1:
            if len(line.strip()) > 0:
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    continue
    return data


def read_lines2(filename, start, end):
    with open(filename, "r") as f:
        data = []
        i = -1
        for line in f:
            i += 1
            if i > end - 1:
                break
            if i > start - 1:
                if len(line.strip()) > 0:
                    try:
                        data.append(json.loads(line))
                    except Exception as e:
                        continue
    return data

if __name__ == "__main__":

    filename = "llmdata/news/test_news.jsonl"

    times, times2 = [], []

    st = time.process_time()
    f = open(filename, "r")
    ed1 = time.process_time()
    times.append(ed1-st)

    for start in range(0, 10000, 1000):
        ed2 = time.process_time()
        data = read_lines(f, start, start+1000)
        ed3 = time.process_time()
        times.append(ed3-ed2)
        print(start, start+1000, len(data))
    f.close()

    print(f"Times:")
    for t in times:
        print(f"{t:.2f}", sep=" ")
    print()


    for start in range(0, 10000, 1000):
        ed2 = time.process_time()
        data = read_lines(filename, start, start+1000)
        ed3 = time.process_time()
        times2.append(ed3-ed2)
        print(start, start+1000, len(data))
    print(f"Times2:")
    for t in times2:
        print(f"{t:.2f}", sep=" ")
    print()