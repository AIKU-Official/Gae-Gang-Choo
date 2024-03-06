import chromadb

import json
from dataclasses import dataclass
from typing import List, Dict, Callable
from collections import defaultdict

from .query_splitter import QuerySplitter, QuerySplitterOpenAI
from .retriever import ReciprocalRetriever
from .embed_generator import EmbedGenerator


@dataclass
class CourseRecommendationOutput:
  course_ids: List[str]
  course_scores: List[float]
  representative_review_ids: Dict[str, List[str]]


class CourseRecommendationPipeline:

  def __init__(
      self,
      db_path,
      ):
    # self.query_splitter = QuerySplitter()
    self.query_splitter = QuerySplitterOpenAI()
    self.multiquery_retriever = ReciprocalRetriever()
    self.embedding_model = EmbedGenerator()
    self.chroma_client = chromadb.PersistentClient(
      path = db_path,
      settings=chromadb.Settings(allow_reset=True, anonymized_telemetry=False)
      )

    self.course_db = self.chroma_client.get_or_create_collection(
        'course',
        embedding_function=self.embedding_model,
        metadata={"hnsw:space": "cosine"}
        )

    self.course_sentence_db = self.chroma_client.get_or_create_collection(
        'course_sentence',
        embedding_function=self.embedding_model,
        metadata={"hnsw:space": "cosine"}
        )

    self.review_db = self.chroma_client.get_or_create_collection(
        'review',
        embedding_function=self.embedding_model,
        metadata={"hnsw:space": "cosine"}
        )

    self.review_sentence_db = self.chroma_client.get_or_create_collection(
        'review_sentence',
        embedding_function=self.embedding_model,
        metadata={"hnsw:space": "cosine"}
        )
    

  def recommend(self, query, verbose: bool=False) -> CourseRecommendationOutput:
    output = self.query_splitter.split(query)
    queries = json.loads(output)

    course_queries = queries["주제관련"]
    review_queries = queries["평가관련"]
    
    if verbose:
      print('내용관련 쿼리:', end='\t')
      print(course_queries)
      print('평가관련 쿼리:', end='\t')
      print(review_queries)

    # course
    course_ids, course_scores, _ = self.multiquery_retriever.query(
      query_texts = course_queries,
      vector_db = self.course_sentence_db,
      relevance_threshold = 0.6
      )
    
    if verbose:
      print('\n 수업의 내용과 관련된 추천 결과:')
      for id in course_ids:
        metadata = self.course_db.get(ids=id)['metadatas'][0]
        print('\t' + metadata['instructor'], '교수님의 ', metadata['course_name'])

    # review
    reranked_ids, reranked_scores, representative_review_ids = self.multiquery_retriever.query(
      query_texts = review_queries,
      course_ids = course_ids,
      vector_db = self.review_sentence_db,
      relevance_threshold = 0.6
      )

    final_score = defaultdict(float)
    for id in reranked_ids:
      final_score[id] += course_scores[course_ids.index(id)] * 0.65
      final_score[id] += reranked_scores[reranked_ids.index(id)] * 0.35

    final_score = sorted(final_score.items(), key=lambda x: x[1], reverse=True)
    course_ids, course_scores = zip(*final_score)

    output = CourseRecommendationOutput(
        course_ids = course_ids,
        course_scores = course_scores,
        representative_review_ids = representative_review_ids
        )

    if verbose:
      print('\n 수업의 리뷰과 관련된 내용으로 리랭킹한 결과:')
      qa_input = self.get_full_output(output)
      for id, info in qa_input.items():
        print(f'\t 수업 제목 : {info["course_name"]}')
        print(f'\t 강의자 : {info["instructor"]}')
        print(f'\t 점수 : {info["score"]}')
        print(f'\t 리뷰 :')
        for review in info["review"]:
          print('\t\t' + review.replace('\n', ' '))
        print('\n')

    full_output = self.get_full_output(output)
    return full_output


  def get_full_output(self, recommendation_output: CourseRecommendationOutput) -> List[Dict]:
    full_output = []

    for i in range(len(recommendation_output.course_ids)):
      course_id = recommendation_output.course_ids[i]
      course_score = recommendation_output.course_scores[i]

      info = self.course_db.get(ids = course_id)
      metadata = info['metadatas'][0]

      review_ids = set()
      for review_sentence_id in recommendation_output.representative_review_ids[course_id]:
        review_id = self.review_sentence_db.get(ids = review_sentence_id)['metadatas'][0]['review_id']
        review_ids.add(review_id)
      review_ids = list(review_ids)

      each_input = {
          'score': course_score,
          'course_name': metadata['course_name'],
          'course_no': metadata['course_no'],
          'course_class': metadata['course_class'],
          'department': metadata['department'],
          'credit': metadata['credit'],
          'course_type': metadata['course_type'],
          'instructor': metadata['instructor'],
          'timeslot': metadata['timeslot'],
          'room': metadata['room'],
          'course_intro': metadata['course_intro'],
          'prerequisite': metadata['prerequisite'],
          'syllabus': metadata['syllabus'],
          'info': info['documents'], # intro + prerequisite + syllabus
          'review': self.review_db.get(ids = review_ids)['documents']
          }
      full_output.append(each_input)

    return full_output