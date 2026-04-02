import json

from typing import List, Any, Optional

from langchain_classic.chains.summarize.chain import load_summarize_chain
from langchain_classic.docstore.document import Document
from langchain_core.language_models import BaseLanguageModel
from llm_call import RoundRobinLLM



class MapReduceSummarizer:
    def __init__(
        self,
        llm: BaseLanguageModel,
        max_chunk: int = 20,
        chain_type: str = "map_reduce",
        verbose: bool = False
    ):
        """
        Production-ready MapReduce summarizer

        Args:
            llm: LangChain compatible LLM
            max_chunk: chunk size for recursive reduce
            chain_type: map_reduce / stuff / refine
            verbose: debug logs
        """
        self.llm = llm
        self.max_chunk = max_chunk
        self.chain_type = chain_type
        self.verbose = verbose

    def _convert_to_documents(self, items: List[Any], field: Optional[str]) -> List[Document]:
        docs = []

        for item in items:
            try:
                if isinstance(item, dict):
                    if field and field in item:
                        text = str(item[field])
                    else:
                        text = json.dumps(item, default=str)
                else:
                    text = str(item)

                docs.append(Document(page_content=text))

            except Exception as e:
  
                docs.append(Document(page_content=str(item)))

        return docs

    def _summarize_docs(self, docs: List[Document]) -> str:
        chain = load_summarize_chain(
            llm=self.llm,
            chain_type=self.chain_type,
            verbose=self.verbose
        )
        return chain.run(docs)

    def summarize(self, items: List[Any], field: Optional[str] = None) -> str:
        """
        Main entry function

        Args:
            items: list of any objects (dict / str / mixed)
            field: optional field to extract

        Returns:
            summarized string
        """

        docs = self._convert_to_documents(items, field)

        # Base case
        if len(docs) <= self.max_chunk:
            return self._summarize_docs(docs)

        # Recursive reduce
        summaries = []

        for i in range(0, len(docs), self.max_chunk):
            chunk = docs[i:i + self.max_chunk]
            chunk_summary = self._summarize_docs(chunk)
            summaries.append({"summary": chunk_summary})

        return self.summarize(summaries, field="summary")