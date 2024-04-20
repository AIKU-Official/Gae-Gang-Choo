import chromadb
import numpy as np
import pandas as pd
from chromadb.config import Settings
from kss import split_sentences
from utils import extract_prefix, preprocess_text, remove_prefix

from vector_db.embed_generator import EmbedGenerator


class VectorDBGenerator:
    def __init__(self, json_path, vetor_db_path):
        self.db_path = vetor_db_path
        self.client = chromadb.PersistentClient(
            path=vetor_db_path,
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
        )
        self.course_df = pd.read_json(json_path)

    def create_course_db(self):
        # Course
        self.client.delete_collection(name="course")

        course_db = self.client.get_or_create_collection(
            "course",
            embedding_function=EmbedGenerator(),
            metadata={"hnsw:space": "cosine"},
        )

        course_db.add(
            ids=self.course_df.id.map(str).values.tolist(),
            documents=self.course_df["course_info"].tolist(),
            metadatas=[
                {
                    "course_id": str(row["id"]),
                    "course_name": str(row["course_name"]),
                    "course_no": str(row["course_no"]),
                    "course_class": str(row["course_class"]),
                    "department": str(row["department"]),
                    "credit": str(row["credit"]),
                    "course_type": str(row["course_type"]),
                    "instructor": str(row["instructor"]),
                    "timeslot": str(row["timeslot"]),
                    "room": str(row["room"]),
                    "course_intro": str(row["course_intro"]),
                    "prerequisite": str(row["prerequisite"]),
                    "syllabus": str(row["syllabus"]),
                }
                for i, row in self.course_df.iterrows()
            ],
        )

        # Course sentences
        course_sentence_df = self.course_df[["id", "course_intro"]]

        course_sentence_df["course_intro"] = course_sentence_df["course_intro"].map(
            split_sentences
        )
        course_sentence_df["course_intro"] = (
            self.course_df["course_name"]
            .apply(extract_prefix)
            .map(lambda x: [x + "을 가르치는 수업"])
            + course_sentence_df["course_intro"]
            + self.course_df["syllabus"]
            .str.split("\n")
            .map(lambda x: list(map(lambda y: remove_prefix(y), x)))
        )

        course_sentence_df = course_sentence_df.explode("course_intro").reset_index(
            drop=True
        )
        course_sentence_df.rename(
            columns={"id": "course_id", "course_intro": "course_sentence"}, inplace=True
        )

        course_sentence_df["course_sentence"] = course_sentence_df[
            "course_sentence"
        ].map(preprocess_text)

        self.client.delete_collection(name="course_sentence")

        course_sentence_db = self.client.get_or_create_collection(
            "course_sentence",
            embedding_function=EmbedGenerator(),
            metadata={"hnsw:space": "cosine"},
        )

        course_sentence_db.add(
            ids=course_sentence_df.index.map(str).values.tolist(),
            documents=course_sentence_df["course_sentence"].tolist(),
            metadatas=[
                {"course_id": str(row["course_id"])}
                for i, row in course_sentence_df.iterrows()
            ],
        )

    def create_review_db(self):
        # Reviews
        review_df = self.course_df[["id", "reviews"]]
        review_df["reviews"] = review_df["reviews"].apply(
            lambda x: [i["text"] for i in x] if x else np.NaN
        )
        review_df = review_df.dropna()
        review_df = review_df.explode("reviews").reset_index(drop=True)

        self.client.delete_collection(name="review")

        review_db = self.client.get_or_create_collection(
            "review",
            embedding_function=EmbedGenerator(),
            metadata={"hnsw:space": "cosine"},
        )

        review_db.add(
            ids=review_df.index.map(str).values.tolist(),
            documents=review_df["reviews"].tolist(),
            metadatas=[
                {
                    "course_id": str(row["id"]),
                }
                for i, row in review_df.iterrows()
            ],
        )

        # Review sentences
        self.client.delete_collection(name="review_sentences")
        review_sentence_df = review_df
        review_sentence_df["reviews"] = review_sentence_df["reviews"].map(
            split_sentences
        )
        review_sentence_df = review_sentence_df.explode("reviews").reset_index()
        review_sentence_df.rename(
            columns={"index": "review_id", "reviews": "review_sentence"}, inplace=True
        )

        review_sentence_df["review_sentence"] = review_sentence_df[
            "review_sentence"
        ].map(preprocess_text)
        review_sentence_db = self.client.get_or_create_collection(
            "review_sentence",
            embedding_function=EmbedGenerator(),
            metadata={"hnsw:space": "cosine"},
        )

        review_sentence_db.add(
            ids=review_sentence_df.index.map(str).values.tolist(),
            documents=review_sentence_df["review_sentence"].tolist(),
            metadatas=[
                {"course_id": str(row["id"]), "review_id": str(row["review_id"])}
                for i, row in review_sentence_df.iterrows()
            ],
        )


if __name__ == "__main__":
    vector_db_generator = VectorDBGenerator(
        json_path="db/course_updated.json", vetor_db_path="vector_db/chroma"
    )
    vector_db_generator.create_course_db()
    vector_db_generator.create_review_db()
