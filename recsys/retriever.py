from collections import defaultdict
from queue import PriorityQueue
from typing import Callable, List, Optional

from scipy.stats import rankdata


class ReciprocalRetriever:
    @staticmethod
    def query(
        query_texts: List[str],
        vector_db: Callable,
        topk: Optional[int] = 8,
        n_example_per_query: Optional[int] = 4,
        course_ids: Optional[List[str]] = None,
        k: Optional[int] = 256,
        relevance_threshold: Optional[float] = 0.5,
    ):

        course_score = defaultdict(list)
        supporting_id = defaultdict(list)

        kwargs = {"query_texts": query_texts}
        if k is not None:
            kwargs["n_results"] = k
        if course_ids is not None:
            kwargs["where"] = {"$or": [{"course_id": i} for i in course_ids]}

        result = vector_db.query(**kwargs)

        course_ids = [
            list(map(lambda x: x["course_id"], i)) for i in result["metadatas"]
        ]
        ids = result["ids"]
        relevances = result["distances"]

        for query_i in range(len(relevances)):
            rel_over_query = defaultdict(list)
            supporting_id_over_query = defaultdict(list)

            queue = PriorityQueue()

            for i in range(len(relevances[query_i])):
                id = ids[query_i][i]
                course_id = course_ids[query_i][i]
                relevance = relevances[query_i][i]
                # 길이가 길어지면... 그만큼 관련없는 문장도 늘어나므로...
                # 평균 연산에는 일정 수준 이상 관련있는 문장만 들어가도록!
                if relevance_threshold and (relevance > relevance_threshold):
                    queue.put((relevance, course_id, id))
                    continue
                rel_over_query[course_id].append(relevance)
                if len(supporting_id_over_query[course_id]) < n_example_per_query:
                    supporting_id_over_query[course_id].append(id)

            # threshold 이슈로 topk보다 적은 경우
            while (not queue.empty()) and (
                len(supporting_id_over_query.values()) < topk
            ):
                relevance, course_id, id = queue.get()
                rel_over_query[course_id].append(relevance)
                supporting_id_over_query[course_id].append(id)

            for key in rel_over_query:
                rel_over_query[key] = sum(rel_over_query[key]) / len(
                    rel_over_query[key]
                )

            ranks = rankdata(list(rel_over_query.values()), method="min", axis=0)
            for i in range(len(ranks)):
                course_id = list(rel_over_query.keys())[i]
                score = 1 / ranks[i]
                course_score[course_id].append(score)

            for key in supporting_id_over_query:
                supporting_id[key] += supporting_id_over_query[key]

        for key in course_score.keys():
            course_score[key] = (
                (sum(course_score[key]) / len(query_texts)) if course_score[key] else 0
            )

        course_id, course_score = zip(
            *sorted(course_score.items(), key=lambda x: x[1], reverse=True)
        )

        return course_id[:topk], course_score[:topk], supporting_id
