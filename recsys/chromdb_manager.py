import chromadb
import numpy as np
import re

from .embed_generator import EmbedGenerator

# TODO: JSON 파일이 아닌 ORM을 사용하여 데이터를 관리하도록 수정
class ChromaDBManager():
    def __init__(self, json_path):
        self.course_df = pd.read_json(json_path)
        self.client = chromadb.Client()

        self.course_vector_db = self._init_collection('course')
        self.review_vector_db = self._init_collection('review')

    def add_course(self):
        self.course_df['course_info'] = self.course_df['course_info'].map(self._preprocess_text)

        self.course_vector_db.add(
            ids = [str(i) for i in range(len(self.course_df))],
            documents = self.course_df["course_info"].tolist(),
            metadatas = [{
                    'course_id': str(row['id']),
                    'course_name': str(row['course_name']),
                    'course_type': str(row['course_type']),
                    'department': str(row['department']),
                    'credit': str(row['credit']),
                    'instructor': str(row['instructor']),
                    'timeslot': str(row['timeslot']),
                    } 
                    for i, row in self.course_df.iterrows()]
        )

    def add_review(self):
        review_df = self.course_df[['id', 'reviews']]
        review_df['reviews'] = review_df['reviews'].apply(lambda x: [i['text'] for i in x] if x else np.NaN)
        review_df = review_df.dropna()
        review_df = review_df.explode('reviews')
        review_df['reviews'] = review_df['reviews'].map(self._preprocess_text)

        self.review_vector_db.add(
            ids = [str(i) for i in range(len(review_df))],
            documents = review_df["reviews"].tolist(),
            metadatas = [{'course_id': i} for i in review_df['id'].map(str).tolist()]
        )

    def _init_collection(self, collection_name):
        return self.client.get_or_create_collection(
            collection_name,
            embedding_function=EmbedGenerator(),
            metadata={"hnsw:space": "cosine"}
        )
    
    def _preprocess_text(text):
        # 한글, 영문, 숫자를 제외한 모든 문자 및 특수 문자 제거
        text = re.sub('[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9]', ' ', text)
        # 연속된 공백을 하나의 공백으로 변환
        text = re.sub('\s+', ' ', text)
        # 양쪽 공백 제거
        text = text.strip()
        return text