##################################################################################################
#                                        SCRIPT OVERVIEW                                         #
#                                                                                                #
# This script provides an interface to query the arXiv API and return scientific articles        #
# matching a user-defined query. It extracts relevant metadata and returns it in a unified       #
# structure suitable for use in LangChain agents or other pipelines.                             #
##################################################################################################

##################################################################################################
#                                            IMPORTS                                             #
##################################################################################################

from typing import Dict, List
from xml.etree import ElementTree as ET

import requests

##################################################################################################
#                                        IMPLEMENTATION                                          #
##################################################################################################


class ArxivClient:
    """
    Interface for querying the arXiv API and retrieving structured scientific article metadata.
    """

    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACES = {"arxiv": "http://arxiv.org/schemas/atom"}

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Searches the arXiv API for scientific articles matching a given free-text query.
        """

        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        response = requests.get(self.BASE_URL, params=params)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.text)
        results = []

        for entry in root.findall("{*}entry"):
            title = (entry.findtext("{*}title") or "").strip()
            abstract = (entry.findtext("{*}summary") or "").strip()
            url = (entry.findtext("{*}id") or "").strip()
            published = (entry.findtext("{*}published") or "").strip()
            doi = (entry.findtext("arxiv:doi", namespaces=self.NAMESPACES) or "").strip()

            results.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "doi": doi,
                    "source": "arXiv",
                    "url": url,
                    "publication_date": published.split("T")[0] if published else "",
                }
            )

        return results


class ArxivTool:
    """
    LangChain-compatible wrapper for the ArxivClient.
    """

    name = "arxiv_search"
    description = "Use this tool to find titles and abstracts from arXiv based on a query. Returns structured JSON."

    def __call__(self, query: str) -> List[Dict]:
        """Invokes the arXiv search using the provided query."""

        return ArxivClient().search(query=query)

    def _run(self, query: str):
        """Synchronous execution wrapper for LangChain compatibility."""

        return self.__call__(query)

    def _arun(self, query: str):
        """Placeholder for asynchronous execution (not implemented)."""

        raise NotImplementedError("Async not supported for ArxivTool.")
