import os
import json
import copy
import time
import tqdm
import random
random.seed(1024)
import argparse

from gemini_api import GeminiAPI
from utils.qwenapi import QwenAPI

from router import Router
from structurizer import Structurizer
from utilizer import Utilizer

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # parser.add_argument("--llm_name", type=str, default="qwen")
    # parser.add_argument("--dataset_name", type=str, default="loong") # data 先暫定為單篇裁定書
    # parser.add_argument("--url", type=str, default="10.32.15.63:1225")
    # parser.add_argument("--router_url", type=str, default=None)
    parser.add_argument("--input_file", type=str, default="test_orders/test_order.txt")
    parser.add_argument("--worker_id", type=int, choices=[0, 1, 2, 3, 4, 5, 6, 7], default=0)
    parser.add_argument("--start_bias", type=int, default=0) # used to manually skip last time error data
    parser.add_argument("--output_path_suffix", type=str, default="")
    parser.add_argument("--max_samples", type=int, default=None,
                    help="只測試前 N 筆資料；None 則跑全部")
    # args = parser.parse_args()

    # for k, v in vars(args).items():
    #     print(f"{k}: {v}")
    # print('\nstart...')

    # main_llm = QwenAPI(url=f"http://{args.url}/v1/chat/completions")
    # if args.router_url is None:
    #     router_llm = QwenAPI(url=f"http://{args.url}/v1/chat/completions")
    # else:
    #     router_llm = QwenAPI(url=f"http://{args.router_url}/v1/chat/completions")

    parser.add_argument("--llm_name", choices=["gemini", "qwen"], default="gemini")
    # Gemini 相關
    parser.add_argument("--api_key", type=str, default=None, help="Gemini API Key")
    parser.add_argument("--model_name", type=str, default="gemini-2.0-flash")
    # Qwen 相關 (保留彈性，必要時仍可用)
    parser.add_argument("--url", type=str, default="10.32.15.63:1225")
    parser.add_argument("--router_url", type=str, default=None)
    # 其他參數...
    args = parser.parse_args()

    print("\nstart...")

    if args.llm_name == "gemini":
        main_llm = GeminiAPI(model_name=args.model_name)
        router_llm = main_llm  # 直接共用；或視情況再 new 一個
    else:  # qwen
        main_llm = QwenAPI(url=f"http://{args.url}/v1/chat/completions")
        router_llm = (main_llm if args.router_url is None
                      else QwenAPI(url=f"http://{args.router_url}/v1/chat/completions"))


    eval_data_path = "./Loong/data/loong_process.jsonl"
    eval_datas = [json.loads(l) for l in open(eval_data_path)]
    random.shuffle(eval_datas)
    eval_datas = eval_datas[200*args.worker_id+args.start_bias : 200*(args.worker_id+1)]
    print(f"len eval_datas: {len(eval_datas)}")

    intermediate_results_dir = f"./intermediate_results/{args.llm_name}/{args.dataset_name}{args.output_path_suffix}"
    os.makedirs(intermediate_results_dir) if not os.path.exists(intermediate_results_dir) else None

    chunk_kb_path = f"{intermediate_results_dir}/chunk_kb"
    graph_kb_path = f"{intermediate_results_dir}/graph_kb"
    table_kb_path = f"{intermediate_results_dir}/table_kb"
    algorithm_kb_path = f"{intermediate_results_dir}/algorithm_kb"
    catalogue_kb_path = f"{intermediate_results_dir}/catalogue_kb"
    os.makedirs(chunk_kb_path) if not os.path.exists(chunk_kb_path) else None
    os.makedirs(graph_kb_path) if not os.path.exists(graph_kb_path) else None
    os.makedirs(table_kb_path) if not os.path.exists(table_kb_path) else None
    os.makedirs(algorithm_kb_path) if not os.path.exists(algorithm_kb_path) else None
    os.makedirs(catalogue_kb_path) if not os.path.exists(catalogue_kb_path) else None

    output_dir = f"./eval_results/{args.llm_name}/{args.dataset_name}{args.output_path_suffix}"
    os.makedirs(output_dir) if not os.path.exists(output_dir) else None
    fw = open(f"{output_dir}/final_output_{args.worker_id}.jsonl", "a")
    fw_error = open(f"{output_dir}/final_output_error_{args.worker_id}.jsonl", "a")
    exiting_data = [json.loads(l) for l in open(f"{output_dir}/final_output_{args.worker_id}.jsonl")]
    exiting_data_ids = [d["id"] for d in exiting_data]    

    router = Router(router_llm)
    structurizer = Structurizer(main_llm, chunk_kb_path, graph_kb_path, table_kb_path, algorithm_kb_path, catalogue_kb_path)
    utilizer = Utilizer(main_llm, chunk_kb_path, graph_kb_path, table_kb_path, algorithm_kb_path, catalogue_kb_path)

    for i, data in enumerate(eval_datas): # data: {"instruction": "", "question": "", "docs": "", "prompt_template": "{},{},{}"}
        if data["id"] in exiting_data_ids:
            print(f"################## Skipping {i}th data existing... ##################")
            continue
        print(f"################## Processing {i}th data... ##################")

        try:
            current_time = time.time()
            fw_intermediate = open(f"{intermediate_results_dir}/{data['id']}.jsonl", "w")

            query = data['prompt_template'].format(instruction=data['instruction'], question=data['question'], docs="......")
            _, titles = structurizer.split_content_and_tile(data['docs'])
            core_content = "The titles of the docs are: " + "\n".join(list(set(titles)))

            # 1. router
            # chosen = router.do_route(query, core_content, data['id'])  
            chosen = 'table'    # 直接選擇 table 作爲 optimal structure
            fw_intermediate.write(json.dumps({"query": query, "chosen": chosen}, ensure_ascii=False) + "\n")
            fw_intermediate.flush()

            # 2. structurizer
            instruction, kb_info = structurizer.construct(query, chosen, data['docs'], data['id'])
            fw_intermediate.write(json.dumps({"instruction": instruction, "kb_info": kb_info}, ensure_ascii=False) + "\n")
            fw_intermediate.flush()

            # 3. utilizer
            subqueries = utilizer.do_decompose(query, kb_info, data['id'])
            fw_intermediate.write(json.dumps({"subqueries": subqueries}, ensure_ascii=False) + "\n")
            fw_intermediate.flush()
            subknowledges = utilizer.do_extract(query, subqueries, chosen, data['id'])
            fw_intermediate.write(json.dumps({"subknowledges": subknowledges}, ensure_ascii=False) + "\n")
            fw_intermediate.flush()
            answer, _, _ = utilizer.do_merge(query, subqueries, subknowledges, chosen, data['id'])
            fw_intermediate.write(json.dumps({"answer": answer}, ensure_ascii=False) + "\n")
            fw_intermediate.flush()
            
            used_time = (time.time() - current_time) / 60
            print(f"level:{data['level']},set:{data['set']},type:{data['type']}")
            print(f"used time: {used_time:.2f} min")

            data['generate_response'] = answer
            data['used_time'] = used_time
            fw.write(json.dumps(data, ensure_ascii=False) + "\n")
            fw.flush()

        except Exception as e:
            print(f"(print in main.py) Error: {e}")
            data['generate_response'] = "meet error"
            data['used_time'] = -100
            fw_error.write(json.dumps(data, ensure_ascii=False) + "\n")
            fw_error.flush()

    print("all done")