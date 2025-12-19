import json

import requests


class Client:
    def __init__(self, tokens):
        self._tokens = tokens
        self._session = requests.Session()

    def query(self, org, query):
        more_pages = True
        cursor = None
        while more_pages:
            page = self._query_page(org, query, cursor)
            yield from page["nodes"]
            page_info = page["pageInfo"]
            more_pages = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

    def _query_page(self, org, query, cursor):
        response = self._session.post(
            "https://api.github.com/graphql",
            headers=self._get_headers(org),
            json={"query": query, "variables": {"cursor": cursor}},
        )

        response.raise_for_status()
        results = response.json()
        self._check_results(results, query)

        return results["data"]["search"]

    def _get_headers(self, org):
        return {
            "Authorization": f"bearer {self._tokens[org]}",
            "User-Agent": "Bennett Metrics",
        }

    def _check_results(self, results, query):
        # The GitHub GraphQL API has a number of ways of indicating that something went wrong, not
        # all of which involve the HTTP status.
        if (
            "data" not in results
            or not results["data"]
            or ("errors" in results and results["errors"])
        ):
            msg = f"""
GraphQL query failed

Query: {query}
Response:
{json.dumps(results, indent=2)}"""
            raise RuntimeError(msg)


PR_QUERY = """
query prs($cursor: String) {
  search(
    query: "org:%s is:pr sort:updated-asc updated:>=%s"
    type: ISSUE
    first: 100
    after: $cursor
  ) {
    nodes {
      ... on PullRequest {
        repository {
          name
        }
        number
        author {
          login
        }
        createdAt
        updatedAt
        closedAt
        mergedAt
        isDraft
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""
