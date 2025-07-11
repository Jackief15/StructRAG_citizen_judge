import json, pathlib
from typing import List, Dict, Set

class Structurizer:
    """產生 <單一> Markdown Boolean Table。
    允許動態欄位；可將現有欄名清單 (existing_factors) 傳入，
    以提示 LLM 優先沿用，避免欄名暴增。
    """

    BASE_COLS = [
        "L1", "L2", "L3", "L4", "L5",
        "涉及共犯", "涉及外國人", "和解", "被害人考量",
    ]

    def __init__(self, llm, table_kb_path: str or pathlib.Path = "table_kb") -> None:
        self.llm = llm
        self.table_kb_path = pathlib.Path(table_kb_path)
        self.table_kb_path.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    def do_construct_table(
        self,
        docs: List[Dict],
        data_id: int,
        instruction: str = "",
        existing_factors: Set[str] or None = None,
    ) -> str:
        """Merge *docs* → prompt LLM → save `data_{id}.md`.
        Returns the **header row** (first line) for logging.
        """
        print(f"data_id {data_id}: build boolean table … (n_docs={len(docs)})")

        core_content = "\n".join(d["document"] for d in docs)
        existing_factors = existing_factors or set()

        # -------------------- Compose prompt --------------------------
        raw_prompt = pathlib.Path("prompts/construct_boolean_table.txt").read_text()
        extra_section = ""
        if existing_factors:
            extra_section = (
                "\n### Existing factors (已出現欄名，請優先沿用)\n"
                + ", ".join(sorted(existing_factors))
                + "\n若無相符再新增新欄。"
            )
        prompt = raw_prompt.format(core=core_content.strip()) + extra_section

        response = self.llm([
            {"role": "user", "content": prompt}
        ], temperature=0.0)
        table_md = response["choices"][0]["message"]["content"].strip()

        # print(f"[DEBUG] Structurizer LLM output ↓\n{response}\n")
        # print(f"[DEBUG] Structurizer LLM output ↓\n{table_md}\n")
        

        # -------------------- Save --------------------------
        out_path = self.table_kb_path / f"data_{data_id}.md"
        out_path.write_text(table_md, encoding="utf-8")

        # -------------------- Return header -----------------
        return table_md.split("\n", 1)[0]


    # def __init__(self, llm, chunk_kb_path, graph_kb_path, table_kb_path, algorithm_kb_path, catalogue_kb_path):
    #     self.llm = llm
    #     self.chunk_kb_path = chunk_kb_path
    #     self.graph_kb_path = graph_kb_path
    #     self.table_kb_path = table_kb_path
    #     self.algorithm_kb_path = algorithm_kb_path
    #     self.catalogue_kb_path = catalogue_kb_path

    # def construct(self, query, chosen, docs, data_id):
    #     print(f"data_id: {data_id}, construct...")

    #     if chosen == "graph":
    #         instruction = f"Based on the given document, construct a graph where entities are the titles of papers and the relation is 'reference', using the given document title as the head and other paper titles as tails."
    #         info_of_graph = self.do_construct_graph(instruction, docs, data_id)
    #         return instruction, info_of_graph
    #     elif chosen == "table":
    #         instruction = f"Query is {query}, please extract relevant complete tables from the document based on the attributes and keywords mentioned in the Query. Note: retain table titles and source information."
    #         info_of_table = self.do_construct_table(instruction, docs, data_id)
    #         return instruction, info_of_table
    #     elif chosen == "algorithm":
    #         instruction = f"Query is {query}, please extract relevant algorithms from the document based on the Query."
    #         info_of_algorithm = self.do_construct_algorithm(instruction, docs, data_id)
    #         return instruction, info_of_algorithm
    #     elif chosen == "catalogue":
    #         instruction = f"Query is {query}, please extract relevant catalogues from the document based on the Query."
    #         info_of_catalogue = self.do_construct_catalogue(instruction, docs, data_id)
    #         return instruction, info_of_catalogue
    #     elif chosen == "chunk":
    #         instruction = f"construct chunk"
    #         info_of_chunk = self.do_construct_chunk(instruction, docs, data_id)
    #         return instruction, info_of_chunk
    #     else:
    #         raise ValueError("chosen should be in ['graph', 'table', 'algorithm', 'catalogue', 'chunk']")

    # def do_construct_graph(self, instruction, docs, data_id):
    #     print(f"data_id: {data_id}, do_construct_graph...")
    #     docs, titles = self.split_content_and_tile(docs)

    #     graphs = []
    #     info_of_graph = ""
    #     raw_prompt = open("prompts/construct_graph.txt", "r").read()
    #     for d, doc in enumerate(docs):
    #         print(f"data_id: {data_id}, do_construct_graph... in doc {d}/{len(docs)} in docs ..")
    #         title = doc['title']
    #         content = doc['document']

    #         prompt = raw_prompt.format(
    #             requirement=instruction, 
    #             raw_content=content,
    #             titles="\n".join(titles)
    #         )
    #         output = self.llm.response(prompt)
    #         info_of_graph += output.split("\n")[0][:128]
    #         graphs.append(f"{title}: {output}")

    #     output_path = f"{self.graph_kb_path}/data_{data_id}.json"
    #     json.dump(graphs, open(output_path, "w"), ensure_ascii=False, indent=4)

    #     return info_of_graph

    # def do_construct_table(self, instruction, docs, data_id):
        # print(f"data_id: {data_id}, do_construct_table...")
        # docs, titles = self.split_content_and_tile(docs)

        # tables = []
        # info_of_table = ""
        # raw_prompt = open("prompts/construct_table.txt", "r").read()
        # for d, doc in enumerate(docs):
        #     print(f"data_id: {data_id}, do_construct_table... in doc {d}/{len(docs)} in docs ..")
        #     title = doc['title']
        #     content = doc['document']
        #     prompt = raw_prompt.format(
        #         instruction=instruction, 
        #         content=content
        #     )
        #     output = self.llm.response(prompt)
        #     info_of_table += output.split("\n")[0][:128]
        #     tables.append(f"{title}: {output}")

        # output_path = f"{self.table_kb_path}/data_{data_id}.json"
        # json.dump(tables, open(output_path, "w"), ensure_ascii=False, indent=4)

        # return info_of_table

        # ★ 改成一次產出「布林條件表」──只保留 1 張
        # print("Table-only mode: build boolean table …")
        # core_content = "\n".join([d['document'] for d in docs])   # 合併所有文件
        # raw_prompt = open("prompts/construct_boolean_table.txt", "r").read()
        # prompt = raw_prompt.format(core=core_content)
        # table_md  = self.llm([{"role":"user","content": prompt}],
        #                        temperature=0.0)["choices"][0]["message"]["content"]
         
        # # 存成 markdown，供 utilizer 直接讀
        # out_path = f"{self.table_kb_path}/data_{data_id}.md"
        # open(out_path, "w").write(table_md)

        # # 首行當 info_of_table 回傳即可
        # info_of_table = table_md.split("\n")[0][:128]
        # return info_of_table

    # def do_construct_chunk(self, instruction, docs, data_id):
    #     print(f"data_id: {data_id}, do_construct_chunk...")
    #     docs, titles = self.split_content_and_tile(docs)

    #     chunks = []
    #     for doc in docs: 
    #         title = doc['title']
    #         content = doc['document']
    #         chunks.append(f"{title}: {content}")

    #     output_path = f"{self.chunk_kb_path}/data_{data_id}.json"
    #     json.dump(chunks, open(output_path, "w"), ensure_ascii=False, indent=4)

    #     info_of_chunk = " ".join(titles)
    #     return info_of_chunk

    # def do_construct_algorithm(self, instruction, docs, data_id):
    #     print(f"data_id: {data_id}, do_construct_algorithm...")
    #     docs, titles = self.split_content_and_tile(docs)

    #     algorithms = []
    #     info_of_algorithm = ""
    #     raw_prompt = open("prompts/construct_algorithm.txt", "r").read()
    #     for d, doc in enumerate(docs):
    #         print(f"data_id: {data_id}, do_construct_algorithm... in doc {d}/{len(docs)} in docs ..")
    #         title = doc['title']
    #         content = doc['document']
    #         prompt = raw_prompt.format(
    #             requirement=instruction, 
    #             raw_content=content
    #         )
    #         output = self.llm.response(prompt)
    #         info_of_algorithm += output.split("\n")[0][:128]
    #         algorithms.append(f"{title}: {output}")

    #     output_path = f"{self.algorithm_kb_path}/data_{data_id}.json"
    #     json.dump(algorithms, open(output_path, "w"), ensure_ascii=False, indent=4) 

    #     return info_of_algorithm
        
    # def do_construct_catalogue(self, instruction, docs, data_id):
    #     print(f"data_id: {data_id}, do_construct_catalogue...")
    #     docs, titles = self.split_content_and_tile(docs)

    #     instruction = instruction.split("Query:\n")[1]

    #     catalogues = []
    #     info_of_catalogue = ""
    #     raw_prompt = open("prompts/construct_catalogue.txt", "r").read()
    #     for d, doc in enumerate(docs):
    #         print(f"data_id: {data_id}, do_construct_catalogue... in doc {d}/{len(docs)} in docs ..")
    #         title = doc['title']
    #         document = doc['document']
            
    #         len_document = len(document)
    #         contents = [document]

    #         for c, content in enumerate(contents):
    #             print(f"data_id: {data_id}, do_construct_catalogue... in doc {d}/{len(docs)} in docs .. in content {c}/{len(contents)} in contents ..")
    #             prompt = raw_prompt.format(
    #                 requirement=instruction, 
    #                 raw_content=content
    #             )
    #             output = self.llm.response(prompt)
    #             info_of_catalogue += output.split("\n")[0][:128]
    #             catalogues.append(f"\n\n{title}: {output}")

    #     output_path = f"{self.catalogue_kb_path}/data_{data_id}.json"
    #     json.dump(catalogues, open(output_path, "w"), ensure_ascii=False, indent=4)

    #     return info_of_catalogue

    # def split_content_and_tile(self, docs_):
    #     docs = []
    #     titles = []
        
    #     raw_doc_list = docs_.strip("<标题起始符>").split("<标题起始符>")

    #     for raw_doc in raw_doc_list:
    #         title = raw_doc.split('<标题终止符>')[0].strip()
    #         content = raw_doc.split('<标题终止符>')[1].strip()

    #         docs.append({'title': title, 'document': content})
    #         titles.append(title)

        # return docs, titles
