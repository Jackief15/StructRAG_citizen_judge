import os
import io
import json
import copy
import time
import tqdm
import random
import pathlib
random.seed(1024)
import argparse
import re
import datetime as dt
import pandas as pd
from typing import Dict, Any, Set, Tuple

# from gemini_api import GeminiAPI
from openai_api import OpenAIAPI
# from claude_api  import ClaudeAPI
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
    parser.add_argument("--util_prompt", type=str, default="prompts/util_boolean.txt")
    
    # LLM 參數
    parser.add_argument("--llm_name",
                    choices=["gemini", "openai", "claude"],
                    default="claude")
    parser.add_argument("--model_name", default="claude-3-7-sonnet-20250219")

    # parser.add_argument("--api_key", type=str, default=None,
    #                     help="可選，若未給則讀 GOOGLE_API_KEY / GEMINI_API_KEY")
    return parser

def auto_cast(txt: str):
    s = str(txt).strip()
    # 空字串或只含 -、_、─ 等視為 missing
    if not s or re.fullmatch(r"[-_─]+", s):
        return None, "empty"

    if s.upper() in {"TRUE", "FALSE"}:
        return s.upper() == "TRUE", "bool"
    try:
        num = float(s) if "." in s else int(s)
        return num, "number"
    except ValueError:
        pass
    try:
        return dt.date.fromisoformat(s), "date"
    except ValueError:
        pass
    return s, "text"

def is_data_line(ln: str) -> bool:
    core = ln.strip().strip("|").replace("-", "").replace(":", "").strip()
    return bool(core)           # 有真正字元才算資料

def run_one_case(
    llm,
    table_dir: pathlib.Path,
    title: str,
    core_text: str,
    idx: int,
    util_prompt_path: pathlib.Path,
    existing_factors: Set[str],
):

    # ---------- Structurizer ----------
    docs = [{"title": title, "document": core_text}]
    Structurizer(llm, table_kb_path=str(table_dir)).do_construct_table(
        docs=docs,
        data_id=idx,
        existing_factors=existing_factors,   # ★ 給 LLM 參考
    )

    # ---------- 讀回 & 取前兩行表格 ----------
    tbl_md  = (table_dir / f"data_{idx}.md").read_text(encoding="utf-8")
    lines   = [ln for ln in tbl_md.splitlines()
               if ln.strip().startswith("|") and ln.count("|") >= 9 and is_data_line(ln)]
    # one_csv = "\n".join(",".join(c.strip() for c in ln.strip("| ").split("|"))
                        # for ln in lines)
    if len(lines) < 2:
        raise ValueError(f"data_id {idx}: markdown 表格缺資料列")

    header, data = lines[0], lines[1]
    table_csv = "\n".join(
        ",".join(c.strip() for c in ln.strip("| ").split("|"))
        for ln in (header, data)
    )
    df_tbl  = pd.read_csv(io.StringIO(table_csv), skipinitialspace=True)
    df_tbl.rename(columns=lambda c: c.strip(), inplace=True)

    BASE = Structurizer.BASE_COLS
    bool_cols: Dict[str, bool]      = {}
    extra_cols: Dict[str, Dict[str, Any]] = {}

    for name, raw_val in df_tbl.iloc[0].items():
        val, typ = auto_cast(str(raw_val))
        if name in BASE:
            bool_cols[name] = bool(val) if typ == "bool" else False
        else:
            if val is not None:
                extra_cols[name] = {"value": val, "type": typ}
            else:
                extra_cols[name] = {"value": "NA", "type": "empty"}

    # 把新出現欄寫回 set 供下一篇 Prompt
    existing_factors.update(extra_cols.keys())

    # ---------- Utilizer ----------
    util = Utilizer(llm, table_kb_path=str(table_dir),
                    prompt_path=str(util_prompt_path))
    verdict, reason = util.infer_boolean(
        query="本案是否仍行國民法官審判？",
        data_id=idx,
        core_text=core_text,
    )

    print(verdict, reason)

    return verdict, reason, bool_cols, extra_cols


def main():
    args = build_parser().parse_args()

    # llm          = GeminiAPI(model_name=args.llm_name)
    if args.llm_name == "gemini":
        llm = GeminiAPI(model_name=args.model_name)
    elif args.llm_name == "openai":   # openai
        llm = OpenAIAPI(model_name=args.model_name)
    else:
        llm = ClaudeAPI(model_name=args.model_name)
    input_path   = pathlib.Path(args.input_file)
    util_prompt  = pathlib.Path(args.util_prompt)
    table_dir    = pathlib.Path("table_kb")
    table_dir.mkdir(exist_ok=True)

    results = []  # 蒐集輸出供寫回 Excel

    if input_path.suffix.lower() in {".txt", ".md"}:
        core = input_path.read_text(encoding="utf-8")
        v, r, tbl = run_one_case(llm, table_dir,
                                 title=input_path.stem,
                                 core_text=core,
                                 idx=0,
                                 util_prompt_path=util_prompt)
        print(tbl)
        print("Verdict:", v, "\nReason:", r)

    elif input_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(input_path, index_col=0)
        for idx, row in df.iterrows():
            print(idx)
            title = str(row.get("裁定字號", f"case-{idx}"))
            core  = str(row.get("reasoning", ""))  # 裁定理由欄
            if not core.strip():
                print(f"⚠️ row {idx}: reasoning 空白，跳過")
                continue
            
            existing_factors: set[str] = set()
            v, r, bool_cols, extra_cols = run_one_case(llm, table_dir, title, core, idx, util_prompt, existing_factors)
            
            row_dict = row.to_dict()
            row_dict.update(bool_cols)   # ← 把 L1~L5 + Accomplice…Victim 9 欄展開
            row_dict.update({            # 再補 verdict / reason
                "verdict": v,
                "reason":  r,
            })
            
            for k, meta in extra_cols.items():        # 動態欄
                row_dict[f"{k}_value"] = meta["value"]
                row_dict[f"{k}_type"]  = meta["type"]
            
            results.append(row_dict)

            print(f"[{idx}] {title} →", v)

        # 將結果寫回新檔
        out_path = input_path.with_stem(input_path.stem + "_withVerdict")
        out_df = pd.DataFrame(results)
        
        # 去掉所有 Unnamed 欄、刪欄名尾空白
        out_df = out_df.loc[:, ~out_df.columns.str.contains("^Unnamed")]
        out_df.rename(columns=lambda c: c.strip(), inplace=True)
        
        out_df.to_excel(out_path, index=False)
        print("✅ All done! Saved to", out_path)

    else:
        raise ValueError("input_file 必須是 .txt/.md 或 .xlsx/.xls")


# -----------------------------------------------------------------------------
# 主流程
# -----------------------------------------------------------------------------

# def main():
#     parser = build_parser()
#     args   = parser.parse_args()

#     # 建立 LLM（Structurizer & Utilizer 共用）
#     llm = GeminiAPI(model_name=args.llm_name)

#     # 讀取裁定書文字
#     data_id = 0
#     input_path = pathlib.Path(args.input_file)
#     core_text  = input_path.read_text(encoding="utf-8")
#     print(f"Loaded {input_path.name} ({len(core_text)} chars)")
#     util_prompt_path = args.util_prompt

#     docs = [{
#         "title": input_path.stem,
#         "document": core_text,
#     }]

#     # Structurizer：產生布林表 (Markdown)
#     table_dir = pathlib.Path("table_kb")
#     table_dir.mkdir(exist_ok=True)

#     structurizer = Structurizer(llm, table_kb_path=str(table_dir))
#     _info = structurizer.do_construct_table(
#         instruction="請依格式填寫下列表格 (TRUE/FALSE)",
#         docs=docs,
#         data_id=data_id,
#     )

#     # Utilizer：Gemini 推論 TRUE / FALSE
#     utilizer = Utilizer(llm, table_kb_path=str(table_dir), prompt_path=util_prompt_path)
#     verdict, reason  = utilizer.infer_boolean(
#         query="本案是否仍行國民法官審判？",
#         data_id=data_id,
#         core_text=core_text
#     )

#     # 布林表
#     table_path = table_dir / f"data_{data_id}.md"   # TABLE_DIR 與 structurizer 使用相同變數
#     table_md   = table_path.read_text(encoding="utf-8")

#     print("\n===== 抽取布林表 =====")
#     print(table_md)                # 直接輸出 Markdown 文字
#     print("\n===== 最終判斷 =====")
#     print("TRUE  → 仍行國民參與", "FALSE → 不行國民參與", sep="\n")
#     print("--------------------")
#     print(verdict)
#     print(reason)
#     print("Pipeline finished (Table‑only StructRAG)")


if __name__ == "__main__":
    main()
