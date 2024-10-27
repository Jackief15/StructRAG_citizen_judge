import json

class Structurizer:
    def __init__(self, llm, chunk_kb_path, graph_kb_path, table_kb_path, algorithm_kb_path, catalogue_kb_path):
        self.llm = llm
        self.chunk_kb_path = chunk_kb_path
        self.graph_kb_path = graph_kb_path
        self.table_kb_path = table_kb_path
        self.algorithm_kb_path = algorithm_kb_path
        self.catalogue_kb_path = catalogue_kb_path

    def construct(self, query, chosen, docs, data_id):
        print(f"data_id: {data_id}, construct...")

        if chosen == "graph":
            instruction = f"Based on the given document, construct a graph where entities are the titles of papers and the relation is 'reference', using the given document title as the head and other paper titles as tails."
            info_of_graph = self.do_construct_graph(instruction, docs, data_id)
            return instruction, info_of_graph
        elif chosen == "table":
            composed_query = "\n".join(query)
            instruction = f"Query is {composed_query}, please extract relevant complete tables from the document based on the attributes and keywords mentioned in the Query. Note: retain table titles and source information."
            info_of_table = self.do_construct_table(instruction, docs, data_id)
            return instruction, info_of_table
        elif chosen == "algorithm":
            composed_query = "\n".join(query)
            instruction = f"Query is {composed_query}, please extract relevant algorithms from the document based on the Query."
            info_of_algorithm = self.do_construct_algorithm(instruction, docs, data_id)
            return instruction, info_of_algorithm
        elif chosen == "catalogue":
            composed_query = "\n".join(query)
            instruction = f"Query is {composed_query}, please extract relevant catalogues from the document based on the Query."
            info_of_catalogue = self.do_construct_catalogue(instruction, docs, data_id)
            return instruction, info_of_catalogue
        elif chosen == "chunk":
            instruction = f"construct chunk"
            info_of_chunk = self.do_construct_chunk(instruction, docs, data_id)
            return instruction, info_of_chunk
        else:
            raise ValueError("chosen should be in ['graph', 'table', 'algorithm', 'catalogue', 'chunk']")

    def do_construct_graph(self, instruction, docs, data_id):
        print(f"data_id: {data_id}, do_construct_graph...")
        docs, titles = self.split_content_and_tile(docs)

        graphs = []
        for d, doc in enumerate(docs):
            print(f"data_id: {data_id}, do_construct_graph... in doc {d}/{len(docs)} in docs ..")
            title = doc['title']
            content = doc['document']

            raw_prompt = open("prompts/construction_graph.txt", "r").read()
            prompt = raw_prompt.format(
                requirement=instruction, 
                raw_content=content,
                titles="\n".join(titles)
            )
            output = self.llm.response(prompt)
            graphs.append(f"{title}: {output}")

        output_path = f"{self.graph_kb_path}/data_{data_id}.json"
        json.dump(graphs, open(output_path, "w"), ensure_ascii=False, indent=4)

        info_of_graph = output.split("\n")[0]
        return info_of_graph

    def do_construct_table(self, instruction, docs, data_id):
        print(f"data_id: {data_id}, do_construct_table...")
        docs, titles = self.split_content_and_tile(docs)

        tables = []
        for d, doc in enumerate(docs):
            print(f"data_id: {data_id}, do_construct_table... in doc {d}/{len(docs)} in docs ..")
            title = doc['title']
            content = doc['document']
            raw_prompt = open("prompts/construction_table.txt", "r").read()
            prompt = raw_prompt.format(
                instruction=instruction, 
                content=content
            )
            output = self.llm.response(prompt)
            tables.append(f"{title}: {output}")

        output_path = f"{self.table_kb_path}/data_{data_id}.json"
        json.dump(tables, open(output_path, "w"), ensure_ascii=False, indent=4)

        info_of_table = output.split("\n")[0]
        return info_of_table

    def do_construct_chunk(self, instruction, docs, data_id):
        print(f"data_id: {data_id}, do_construct_chunk...")
        docs, titles = self.split_content_and_tile(docs)

        chunks = []
        for doc in docs: 
            title = doc['title']
            content = doc['document']
            chunks.append(f"{title}: {content}")

        output_path = f"{self.chunk_kb_path}/data_{data_id}.json"
        json.dump(chunks, open(output_path, "w"), ensure_ascii=False, indent=4)

        info_of_chunk = " ".join(titles)
        return info_of_chunk

    def do_construct_algorithm(self, instruction, docs, data_id):
        print(f"data_id: {data_id}, do_construct_algorithm...")
        docs, titles = self.split_content_and_tile(docs)

        algorithms = []
        for d, doc in enumerate(docs):
            print(f"data_id: {data_id}, do_construct_algorithm... in doc {d}/{len(docs)} in docs ..")
            title = doc['title']
            content = doc['document']
            raw_prompt = open("prompts/construction_algorithm.txt", "r").read()
            prompt = raw_prompt.format(
                requirement=instruction, 
                raw_content=content
            )
            output = self.llm.response(prompt)
            algorithms.append(f"{title}: {output}")

        output_path = f"{self.algorithm_kb_path}/data_{data_id}.json"
        json.dump(algorithms, open(output_path, "w"), ensure_ascii=False, indent=4) 

        info_of_algorithm = output.split("\n")[0]
        return info_of_algorithm
        
    def do_construct_catalogue(self, instruction, docs, data_id):
        print(f"data_id: {data_id}, do_construct_catalogue...")
        docs, titles = self.split_content_and_tile(docs)

        instruction = instruction.split("Query:\n")[1]

        catalogues = []
        for d, doc in enumerate(docs):
            print(f"data_id: {data_id}, do_construct_catalogue... in doc {d}/{len(docs)} in docs ..")
            title = doc['title']
            document = doc['document']
            raw_prompt = open("prompts/construction_catalogue.txt", "r").read()
            
            len_document = len(document)
            contents = [document]

            for c, content in enumerate(contents):
                print(f"data_id: {data_id}, do_construct_catalogue... in doc {d}/{len(docs)} in docs .. in content {c}/{len(contents)} in contents ..")
                prompt = raw_prompt.format(
                    requirement=instruction, 
                    raw_content=content
                )
                output = self.llm.response(prompt)
                catalogues.append(f"\n\n{title}: {output}")

        output_path = f"{self.catalogue_kb_path}/data_{data_id}.json"
        json.dump(catalogues, open(output_path, "w"), ensure_ascii=False, indent=4)

        info_of_catalogue = output.split("\n")[0]
        return info_of_catalogue

    def split_content_and_tile(self, docs_):
        docs = []
        titles = []
        for d in docs_:
            title = d.split('\n')[0].strip().strip('\n')
            content = d.split('\n')[1]

            docs.append({'title': title, 'document': content})
            titles.append(title)

        return docs, titles
