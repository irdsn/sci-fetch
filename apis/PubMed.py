##################################################################################################
#                                        PUBMED API CLIENT                                       #
#                                                                                                #
# This script provides functionality to search and fetch scientific articles from PubMed.        #
# It exposes a client class and a LangChain tool wrapper for autonomous integration.             #
##################################################################################################

##################################################################################################
#                                            IMPORTS                                             #
##################################################################################################

import requests
from typing import List, Dict
from xml.etree import ElementTree as ET
from dateutil import parser

##################################################################################################
#                                        IMPLEMENTATION                                          #
##################################################################################################

def _find_text(element: ET.Element | None, path: str) -> str:
    """Returns stripped text for an ElementTree path, or an empty string."""

    if element is None:
        return ""

    node = element.find(path)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def extract_pubmed_date(article: ET.Element) -> str:
    """
    Extracts the publication date from a PubMed article element.

    This function attempts multiple strategies to retrieve a valid publication date from
    different XML fields. It returns the date in 'YYYY-MM-DD' or 'YYYY-MM' format. If
    no date can be extracted, it returns an empty string.

    Args:
        article: A PubMedArticle XML element.

    Returns:
        str: Formatted publication date or empty string if not found.
    """

    try:
        article_date = article.find("./MedlineCitation/Article/ArticleDate")
        if article_date is not None:
            y = _find_text(article_date, "Year")
            m = _find_text(article_date, "Month")
            d = _find_text(article_date, "Day")
            return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    except Exception:
        pass

    try:
        completed = article.find("./MedlineCitation/DateCompleted")
        y = _find_text(completed, "Year")
        m = _find_text(completed, "Month")
        return f"{y}-{m.zfill(2)}-01"
    except Exception:
        pass

    try:
        date_str = _find_text(
            article,
            "./MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate",
        )
        dt = parser.parse(date_str, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return ""

class PubMedClient:
    """
    Client for interacting with the PubMed API to search and retrieve scientific articles.

    This client provides methods to perform keyword-based search queries and to fetch
    metadata for articles using their unique IDs. It parses titles, abstracts, DOIs,
    publication dates, and constructs URLs for referencing.

    Attributes:
        BASE_URL (str): URL endpoint for PubMed search queries.
        FETCH_URL (str): URL endpoint for fetching article metadata.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def search(self, query: str, max_results: int = 10) -> List[str]:
        """
        Searches the PubMed database for articles matching the given query.

        Returns a list of PubMed article IDs matching the search criteria.

        Args:
            query (str): Search query string.
            max_results (int): Maximum number of results to return (default is 10).

        Returns:
            List[str]: List of PubMed article identifiers.
        """

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "pub+date"
        }
        resp = requests.get(self.BASE_URL, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("esearchresult", {}).get("idlist", [])
        return []

    def fetch_details(self, ids: List[str]) -> List[Dict]:
        """
        Retrieves metadata for a list of PubMed article IDs.

        Parses the XML response and extracts structured inputs for each article,
        including title, abstract, DOI, publication date, and source URL.

        Args:
            ids (List[str]): List of PubMed article identifiers.

        Returns:
            List[Dict]: List of dictionaries with article metadata.
        """

        if not ids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml"
        }
        resp = requests.get(self.FETCH_URL, params=params)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.text)
        articles = []
        for article in root.findall(".//PubmedArticle"):
            title = _find_text(article, "./MedlineCitation/Article/ArticleTitle") or None
            abstract = _find_text(article, "./MedlineCitation/Article/Abstract/AbstractText") or None
            article_id = _find_text(article, "./MedlineCitation/PMID")
            doi = None
            for location_id in article.findall(".//ELocationID"):
                if location_id.attrib.get("EIdType") == "doi" and location_id.text:
                    doi = location_id.text.strip()
                    break
            pub_date = extract_pubmed_date(article)

            articles.append({
                "title": title,
                "abstract": abstract,
                "doi": doi,
                "source": "PubMed",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}",
                "publication_date": pub_date
            })
        return articles

class PubMedTool:
    """
    LangChain-compatible wrapper for using the PubMedClient as a search tool.

    This tool enables integration of PubMed search functionality within
    autonomous agent environments or structured pipelines.

    Attributes:
        name (str): Tool name used for agent identification.
        description (str): Description shown to the agent for tool selection.
    """

    name = "pubmed_search"
    description = "Use this tool to find titles and abstracts from PubMed based on a query. Returns structured JSON."

    def __call__(self, query: str) -> List[Dict]:
        """
        Executes a PubMed search and retrieves article metadata for matching results.

        Args:
            query (str): Free-text search query.

        Returns:
            List[Dict]: List of metadata dictionaries for matching articles.
        """

        client = PubMedClient()
        ids = client.search(query=query)
        return client.fetch_details(ids)

    def _run(self, query: str):
        """
        Synchronous execution wrapper for LangChain compatibility.

        Args:
            query (str): Search query string.

        Returns:
            List[Dict]: Metadata results from the PubMedClient.
        """

        return self.__call__(query)

    def _arun(self, query: str):
        """
        Placeholder for asynchronous execution (not implemented).

        Raises:
            NotImplementedError: Async support is not available.
        """

        raise NotImplementedError("Async not supported for PubMedTool.")
