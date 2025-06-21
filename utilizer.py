# import json
import pathlib, io, pandas as pd
from typing import Dict

class Utilizer():
    """Boolean-table Utilizer: read table markdown, prompt LLM, return bool."""

    LAW_TEXT = """\
    應行國民參與審判之案件，有下列情形之一者，法院得依職權或當事人、辯護人、輔佐人之聲請，於聽取當事人、辯護人、輔佐人之意見後，裁定不行國民參與審判：
    一、有事實足認行國民參與審判有難期公正之虞。
    二、對於國民法官、備位國民法官本人或其配偶、八親等內血親、五親等內姻親或家長、家屬之生命、身體、自由、名譽、財產有致生危害之虞。
    三、案件情節繁雜或需高度專業知識，非經長久時日顯難完成審判。
    四、被告就被訴事實為有罪之陳述，經審判長告知被告通常審判程序之旨，且依案件情節，認不行國民參與審判為適當。
    五、其他有事實足認行國民參與審判顯不適當。
    """

    def __init__(self, llm, table_kb_path: str or pathlib.Path,
                 prompt_path: str = "prompts/util_boolean.txt"):
        self.llm = llm
        self.table_kb_path = pathlib.Path(table_kb_path)
        self.prompt_path = pathlib.Path(prompt_path)
        if not self.prompt_path.exists():
            raise FileNotFoundError(self.prompt_path)

    # ------------------------------------------------------------------
    def infer_boolean(self, query: str, core_text: str, data_id: int or str) -> bool:
        """Read data_<id>.md -> ask LLM -> return True/False."""
        md_file = self.table_kb_path / f"data_{data_id}.md"
        if not md_file.exists():
            raise FileNotFoundError(md_file)
        table_md = md_file.read_text(encoding="utf-8")

        raw_prompt = self.prompt_path.read_text(encoding="utf-8")
        prompt = raw_prompt.format(table=table_md.strip(), query=query, core=core_text, statute=self.LAW_TEXT)

        reply = self.llm([
            {"role": "user", "content": prompt}
        ], temperature=0.0)["choices"][0]["message"]["content"]

        first_token = reply.strip().split()[0].upper()
        self.response = reply  # 與 QwenAPI 介面對齊
        reason = reply.strip()[len(reply.strip().split()[0]):].lstrip()
        return first_token.startswith("T"), reason
    
    # def __init__(self, llm, chunk_kb_path, graph_kb_path, table_kb_path, algorithm_kb_path, catalogue_kb_path):
    #     self.llm = llm
    #     self.chunk_kb_path = chunk_kb_path
    #     self.graph_kb_path = graph_kb_path
    #     self.table_kb_path = table_kb_path
    #     self.algorithm_kb_path = algorithm_kb_path
    #     self.catalogue_kb_path = catalogue_kb_path

    # def do_decompose(self, query, kb_info, data_id):
    #     print(f"data_id: {data_id}, do_decompose...")

    #     raw_prompt = open("prompts/decompose.txt", "r").read()
    #     prompt = raw_prompt.format(
    #         query=query, 
    #         kb_info=kb_info
    #     )
    #     output = self.llm.response(prompt) 
    #     subqueries = output.split("\n")

    #     return subqueries

    # def do_extract(self, query, subqueries, chosen, data_id, extra_instruction=None):
    #     print(f"data_id: {data_id}, extraction...")

    #     if extra_instruction != None:
    #         subqueries = [subquery + extra_instruction for subquery in subqueries]
        
    #     if chosen == "chunk":
    #         subknowledges = self.do_extract_chunk(query, subqueries, data_id)
    #     elif chosen == "table":
    #         subknowledges = self.do_extract_table(query, subqueries, data_id)
    #     elif chosen == "graph":
    #         subknowledges = self.do_extract_graph(query, subqueries, data_id)
    #     elif chosen == "algorithm":
    #         subknowledges = self.do_extract_algorithm(query, subqueries, data_id)
    #     elif chosen == "catalogue":
    #         subknowledges = self.do_extract_catalogue(query, subqueries, data_id)
    #     else:
    #         raise ValueError("chosen should be in ['chunk', 'table', 'graph', 'algorithm', 'catalogue']")

    #     return subknowledges

    # def do_extract_chunk(self, query, subqueries, data_id):
    #     chunks = json.load(open(f"{self.chunk_kb_path}/data_{data_id}.json"))

    #     composed_query = "\n".join(subqueries) 

    #     subknowledges = []
    #     for c, chunk in enumerate(chunks):
    #         print(f"retrieve chunk {c}/{len(chunks)} in chunks ..")

    #         prompt = f"Instruction:\nAnswer the Query based on the given Document.\n\nQuery:\n{composed_query}\n\nDocument:\n{chunk}\n\nOutput:"
    #         tmp_output = self.llm.response(prompt)
    #         title = chunk.split(":")[0]
    #         subknowledges.append(f"Retrieval result for {title}: {tmp_output}")

    #     return subknowledges   

    # def do_extract_table(self, query, subqueries, data_id):
    #     print(f"data_id: {data_id}, do_extract_table...")

    #     tables = json.load(open(f"{self.table_kb_path}/data_{data_id}.json"))
    #     tables_content = ""
    #     for t, table in enumerate(tables):
    #         tables_content += f"Table {t+1}:\n{table}\n\n"

    #     subknowledges = []
    #     for s, subquery in enumerate(subqueries):
    #         print(f"data_id: {data_id}, do_extract_table... in subquery {s}/{len(subqueries)} in subqueries ..")
    #         prompt = f"Instruction:\nThe following Tables show multiple independent tables built from multiple documents.\nFilter these tables according to the query, retaining only the table information that helps answer the query.\nNote that you need to analyze the attributes and entities mentioned in the query and filter accordingly.\nThe information needed to answer the query must exist in one or several tables, and you need to check these tables one by one.\n\nTables:{tables_content}\n\nQuery:{subquery}\n\nOutput:"
    #         retrieval = self.llm.response(prompt)
    #         subknowledges.append(retrieval)

    #     return subknowledges
    
    # def do_extract_graph(self, query, subqueries, data_id):
    #     print(f"data_id: {data_id}, do_extract_graph...")

    #     graphs = json.load(open(f"{self.graph_kb_path}/data_{data_id}.json"))
    #     graphs_content = "\n\n".join(graphs)

    #     subknowledges = []
    #     for s, subquery in enumerate(subqueries):
    #         print(f"data_id: {data_id}, do_extract_graph... in subquery {s}/{len(subqueries)} in subqueries ..")
    #         prompt = f"Instruction: According to the query, filter out the triples from all triples in the graph that can help answer the query.\nNote, carefully analyze the entities and relationships mentioned in the query and filter based on this information.\n\nGraphs:{graphs_content}\n\nQuery:{subquery}\n\nOutput:"
    #         retrieval = self.llm.response(prompt)
    #         subknowledges.append(retrieval)

    #     return subknowledges

    # def do_extract_algorithm(self, query, subqueries, data_id):
    #     print(f"data_id: {data_id}, do_extract_algorithm...")

    #     algorithms = json.load(open(f"{self.algorithm_kb_path}/data_{data_id}.json"))
    #     algorithms_content = "\n\n".join(algorithms)

    #     subknowledges = []
    #     for s, subquery in enumerate(subqueries):
    #         print(f"data_id: {data_id}, do_extract_algorithm... in subquery {s}/{len(subqueries)} in subqueries ..")
    #         prompt = f"Instruction: According to the query, filter out information from algorithm descriptions that can help answer the query.\nNote, carefully analyze the entities and relationships mentioned in the query and filter based on this information.\n\nAlgorithms:{algorithms_content}\n\nQuery:{subquery}\n\nOutput:"
    #         retrieval = self.llm.response(prompt)
    #         subknowledges.append(retrieval)

    #     return subknowledges

    # def do_extract_catalogue(self, query, subqueries, data_id):
    #     print(f"data_id: {data_id}, do_extract_catalogue...")

    #     catalogues = json.load(open(f"{self.catalogue_kb_path}/data_{data_id}.json"))
    #     catalogues_content = "\n\n".join(catalogues)

    #     subknowledges = []
    #     for s, subquery in enumerate(subqueries):
    #         print(f"data_id: {data_id}, do_extract_catalogue... in subquery {s}/{len(subqueries)} in subqueries ..")
    #         prompt = f"Instruction: According to the query, filter out information from the catalogue that can help answer the query.\nNote, carefully analyze the entities and relationships mentioned in the query and filter based on this information.\n\nCatalogues:{catalogues_content}\n\nQuery:{subquery}\n\nOutput:"
    #         retrieval = self.llm.response(prompt)
    #         subknowledges.append(retrieval)

    #     return subknowledges

    # def do_merge(self, query, subqueries, subknowledges, chosen, data_id):
    #     print(f"data_id: {data_id}, do_merge...")

    #     retrieval_of_chunk = ""
    #     retrieval_of_graph = ""
    #     retrieval_of_table = ""
    #     retrieval_of_algorithm = ""
    #     retrieval_of_catalogue = ""

    #     if chosen == "chunk":
    #         subknowledges = "\n".join(subknowledges)
    #         retrieval_of_chunk += f"Subquery: {query}\nRetrieval results:\n{subknowledges}\n\n"
    #     elif chosen == "table":
    #         for subquery, subknowledge in zip(subqueries, subknowledges):
    #             retrieval_of_table += f"Subquery: {subquery}\nRetrieval results:\n{subknowledge}\n\n"
    #     elif chosen == "graph":
    #         for subquery, subknowledge in zip(subqueries, subknowledges):
    #             retrieval_of_graph += f"Subquery: {subquery}\nRetrieval results:\n{subknowledge}\n\n"
    #     elif chosen == "algorithm":
    #         for subquery, subknowledge in zip(subqueries, subknowledges):
    #             retrieval_of_algorithm += f"Subquery: {subquery}\nRetrieval results:\n{subknowledge}\n\n"
    #     elif chosen == "catalogue":
    #         subknowledges = "\n".join(subknowledges)
    #         retrieval_of_catalogue += f"Subquery: {query}\nRetrieval results:\n{subknowledges}\n\n"
    #     else:
    #         raise ValueError("chosen should be in ['chunk', 'table', 'graph', 'algorithm', 'catalogue']")

    #     decision = "No"
    #     new_query = "No"
    #     instruction = "1. Answer the Question based on retrieval results. \n2. Find the relevant information from given retrieval results and output as detailed, specific, and lengthy as possible. \n3. The output must be a coherent and smooth piece of text."
    #     prompt = f"Instruction:\n{instruction}\n\nQuestion:\n{query}\n\nRetrieval:\n{retrieval_of_chunk}{retrieval_of_graph}{retrieval_of_table}{retrieval_of_algorithm}{retrieval_of_catalogue}"

    #     answer = self.llm.response(prompt)

    #     return answer, decision, new_query
