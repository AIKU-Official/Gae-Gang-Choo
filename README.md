
## How to start

### Generate vector DB
```bash
python vector_db/vector_db_manager.py
```

### Run Demo
```bash
python demo.py
```


## 소개
🎉 **2024년 겨울학기 AIKU Conference 장려상 수상!**

> 당신이 원하는 꿀강 혹은 명강, 찾아드립니다

어떤 강의가 나에게 적절할지 이리저리 리뷰 검색 사이트와 커뮤니티를 돌아다녔을 학생들… 강의에 대한 정보와 리뷰들을 고려해, 언어모델이 친절하게 추천해주고 설명해준다면 좀 더 수월한 수강 신청이 되지 않을까요? 본 프로젝트는 언어모델을 활용한 고려대학교 강의 추천 시스템을 만들어보고자 하는 생각으로부터 시작됐습니다.

![pipeline.npg](https://github.com/AIKU-Official/Gae-Gang-Choo/blob/main/assets/screenshot.png)

## 목표

사용자의 요구를 충실히 반영한, 고려대학교 강의 추천을 할 수 있는 언어모델을 만들자

- 유저의 쿼리를 추천에 충실히 반영하기 위한 쿼리 분석 및 재생성
- 언어모델의 External Knowledge 접근을 위한 시스템 구축
- LLM의 In-Context Learning 능력을 활용한 적절한 Prompting 탐색

## 데이터셋

| **데이터셋** | **설명** |
| --- | --- |
| 고려대학교 수강신청 사이트
(https://sugang.korea.ac.kr/) | 23-1학기 컴퓨터학과 전공 과목 56개에 대한 강의 정보 수집 |
| 고려대학교 강의 리뷰 공유 사이트 | 56개 전공 과목에 대한 강의리뷰 수집 |

## 모델링

Vector DB와 문장 임베딩 모델, 검색 알고리즘, LLM이 전체 시스템을 구성합니다.

![pipeline.npg](https://github.com/AIKU-Official/Gae-Gang-Choo/blob/main/assets/pipeline.png)

- 검색 & 랭킹 알고리즘
    - LLM에게 적절한 Context를 제공해주는 것이 위 시스템의 가장 중요한 파트라고 할 수 있습니다. 본 프로젝트에서는 Multi-Query 방법론과 Reciprocal Rank Fusion 알고리즘을 사용했습니다. 유저의 쿼리에 대해 종합적으로 고려한, 높은 품질의 검색 결과를 반환하기 위해 사용하였습니다.
- LLM
    - LLM은 위 시스템에서 2가지 역할을 하게 됩니다.
        1. 유저의 쿼리를 강의 정보 관련 쿼리 N개, 강의 리뷰 관련 쿼리 M개로 나누는 쿼리 Splitter 역할
        2. 검색 & 랭킹 알고리즘이 제공해준 Context에 기반한 강의 추천과 설명
    - 이를 위한 프롬프팅 템플릿을 자체 제작하여 사용하였습니다.

## 훈련 및 평가

### 훈련

본 프로젝트는 Ram *et al (2023)* 에서 제안한 RALM 구조를 사용하여 모델의 Parameter를 학습시키는 과정을 거치지 않았습니다. 강의 추천을 위한 LLM이 가능하도록 Instruction Tuning(a.k.a Prompt Engineering) 방식으로 모델을 강의 추천 Task를 위해 조정하였습니다.

*관련 페이퍼

[In-Context Retrieval-Augmented Language Models](https://arxiv.org/abs/2302.00083)

### 평가

정량 평가를 정의하기 어려운 작업인 만큼, 팀원 간 정성 평가를 통해 추천 및 summary 생성 성능을 평가하였습니다.

## 한계 분석

1. LLM 특성상 비교적 무게가 작은 10.7B 모델임에도 Inference(generation)에 걸리는 시간이 상당함을 확인할 수 있었습니다.
2. 리뷰 사이트의 서버 부담을 피하기 위해, 크롤링 범위를 제한하여 추천 및 설명할 수 있는 강의가 제한되어있습니다.

## 후속 프로젝트

1. 성능-모델 무게 간 Trade-off 관계를 해결할 수 있는 small LLM 
2. 비단 강의 추천 뿐만 아니라, 더 복잡한 Task를 수행할 수 있는 LLM Prompt Engineering 방법론
