import os
import json
import copy
import time
import tqdm
import random
import pathlib
random.seed(1024)
import argparse

from gemini_api import GeminiAPI
# from utils.qwenapi import QwenAPI

# from router import Router
from structurizer import Structurizer
from utilizer import Utilizer

# -----------------------------------------------------------------------------
# CLI 參數設定
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Table‑only StructRAG — 判斷裁定書是否仍行國民法官審判")

    parser.add_argument("--input_file", type=str, required=True,
                        help="裁定書純文字檔 (UTF‑8) ‑ e.g. test_order.txt")

    # Gemini LLM 參數
    parser.add_argument("--llm_name", type=str, default="gemini-2.0-flash",
                        help="Gemini 模型，如 gemini‑1.5‑pro / 2.5‑pro / flash")
    # parser.add_argument("--api_key", type=str, default=None,
    #                     help="可選，若未給則讀 GOOGLE_API_KEY / GEMINI_API_KEY")

    parser.add_argument("--util_prompt", type=str, default="prompts/util_boolean.txt")
    return parser


# -----------------------------------------------------------------------------
# 主流程
# -----------------------------------------------------------------------------

def main():
    parser = build_parser()
    args   = parser.parse_args()

    # 建立 LLM（Structurizer & Utilizer 共用）
    llm = GeminiAPI(model_name=args.llm_name)

    # 讀取裁定書文字
    data_id = 0
    input_path = pathlib.Path(args.input_file)
    core_text  = input_path.read_text(encoding="utf-8")
    print(f"Loaded {input_path.name} ({len(core_text)} chars)")
    util_prompt_path = args.util_prompt

    docs = [{
        "title": input_path.stem,
        "document": core_text,
    }]

    # Structurizer：產生布林表 (Markdown)
    table_dir = pathlib.Path("table_kb")
    table_dir.mkdir(exist_ok=True)

    structurizer = Structurizer(llm, table_kb_path=str(table_dir))
    _info = structurizer.do_construct_table(
        instruction="請依格式填寫下列表格 (TRUE/FALSE)",
        docs=docs,
        data_id=data_id,
    )

    # Utilizer：Gemini 推論 TRUE / FALSE
    utilizer = Utilizer(llm, table_kb_path=str(table_dir), prompt_path=util_prompt_path)
    verdict, reason  = utilizer.infer_boolean(
        query="本案是否仍行國民法官審判？",
        data_id=data_id,
        core_text=core_text
    )

    # 布林表
    table_path = table_dir / f"data_{data_id}.md"   # TABLE_DIR 與 structurizer 使用相同變數
    table_md   = table_path.read_text(encoding="utf-8")

    print("\n===== 抽取布林表 =====")
    print(table_md)                # 直接輸出 Markdown 文字
    print("\n===== 最終判斷 =====")
    print("TRUE  → 仍行國民參與", "FALSE → 不行國民參與", sep="\n")
    print("--------------------")
    print(verdict)
    print(reason)
    print("Pipeline finished (Table‑only StructRAG)")


if __name__ == "__main__":
    main()
