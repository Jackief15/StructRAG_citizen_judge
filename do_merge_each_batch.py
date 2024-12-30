import os
import json

model_name = "qwen"
git_hash = ""
suffix = ""

if os.path.exists(f"./Loong/output/{model_name}/loong_generate.jsonl"):
    raise ValueError(f"File already exists: ./Loong/output/{model_name}/loong_generate.jsonl")
if os.path.exists(f"./Loong/output/{model_name}/loong_evaluate.jsonl"):
    raise ValueError(f"File already exists: ./Loong/output/{model_name}/loong_evaluate.jsonl")

total_datas = []

dir_path = f"./eval_results{git_hash}/{model_name}/loong{suffix}"

if os.path.exists(f"{dir_path}/final_output_0.jsonl"):
    a_s = [json.loads(line) for line in open(f"{dir_path}/final_output_0.jsonl")]
    print(len(a_s))
    total_datas += a_s

if os.path.exists(f"{dir_path}/final_output_1.jsonl"):
    b_s = [json.loads(line) for line in open(f"{dir_path}/final_output_1.jsonl")]
    print(len(b_s))
    total_datas += b_s

if os.path.exists(f"{dir_path}/final_output_2.jsonl"):
    c_s = [json.loads(line) for line in open(f"{dir_path}/final_output_2.jsonl")]
    print(len(c_s))
    total_datas += c_s

if os.path.exists(f"{dir_path}/final_output_3.jsonl"):
    d_s = [json.loads(line) for line in open(f"{dir_path}/final_output_3.jsonl")]
    print(len(d_s))
    total_datas += d_s

if os.path.exists(f"{dir_path}/final_output_4.jsonl"):
    e_s = [json.loads(line) for line in open(f"{dir_path}/final_output_4.jsonl")]
    print(len(e_s))
    total_datas += e_s

if os.path.exists(f"{dir_path}/final_output_5.jsonl"):
    f_s = [json.loads(line) for line in open(f"{dir_path}/final_output_5.jsonl")]
    print(len(f_s))
    total_datas += f_s

if os.path.exists(f"{dir_path}/final_output_6.jsonl"):
    g_s = [json.loads(line) for line in open(f"{dir_path}/final_output_6.jsonl")]
    print(len(g_s))
    total_datas += g_s

if os.path.exists(f"{dir_path}/final_output_7.jsonl"):
    h_s = [json.loads(line) for line in open(f"{dir_path}/final_output_7.jsonl")]
    print(len(h_s))
    total_datas += h_s

print("len(total_datas)", len(total_datas))

fw = open(f"./Loong/output/{model_name}/loong_generate.jsonl", "w")
for t in total_datas:
    fw.write(json.dumps(t) + "\n")
fw.close()