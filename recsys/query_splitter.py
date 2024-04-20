import os

import torch
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from openai import OpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


class QuerySplitter:

    def __init__(
        self,
        pretrained_model_name="LDCC/LDCC-SOLAR-10.7B",
    ):

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name,
            torch_dtype="auto",
            quantization_config=quantization_config,
            low_cpu_mem_usage=True,
            ignore_mismatched_sizes=True,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name, use_fast=True
        )

        self.prompt_template = self._create_prompt_template()

    def _create_prompt_template(self):
        template = """
    예시:

    질문:
    {example_query}

    답변:
    {example_answer}

    위의 형식과 동일한 형식으로 다음 질문에 대한 답변해주세요.

    질문:
    {query}

    답변:
    """
        example_query = "나는 인공지능과 관련된 수업을 듣고 싶어. 또, 수업 안에서 인공지능의 원론적인 내용보다는 딥러닝 관련 내용을 배우고싶어. 빡세더라도 얻어가는게 많았으면 좋겠어. 그리고 교수님이 학점을 잘 주시고 강의력이 좋으면 좋겠어."
        example_answer = '{"주제관련": ["인공지능과 관련된 수업", "수업 안에서 인공지능의 원론적인 내용보다는 딥러닝 관련 내용을 배우는 수업"],\
    "평가관련": ["빡세더라도 얻어가는게 많은 수업", "교수님이 학점을 잘주시는 수업", "교수님이 강의력이 좋은 수업"]}'
        prompt_template = PromptTemplate(
            template=template,
            input_variables=["query"],
            partial_variables={
                "example_query": example_query,
                "example_answer": example_answer,
            },
        )
        return prompt_template

    def _get_model_input(self, query):
        _input = self.prompt_template.format_prompt(query=query.strip())
        conversation = [
            {
                "role": "system",
                "content": "너는 문장을 '수업의 강의 주제과 관련된 문장', '수업의 평가와 관련된 문장'으로 분류하는 문장 분류 전문가야.",
            },
            {"role": "user", "content": _input.to_string()},
        ]
        prompt = self.tokenizer.apply_chat_template(
            conversation, tokenize=False, add_generation_prompt=True
        )
        return prompt

    def _postprocess_output(self, output_text, inst_token="[/INST]", eos_token="</s>"):
        output_text = output_text[
            output_text.find(inst_token) + len(inst_token) : output_text.find(eos_token)
        ]
        output_text = output_text[output_text.find("{") : output_text.find("}") + 1]

        output_text = output_text.replace(
            ' "', '"'
        )  # Tokenizer때문에 공백이 더해지는 현상 해결
        return output_text

    def split(self, query):
        prompt = self._get_model_input(query)

        max_new_tokens = (
            len(
                self.tokenizer(
                    query, return_tensors="pt", add_special_tokens=False
                ).input_ids[0]
            )
            + 32
        )

        inputs = self.tokenizer(
            prompt, return_tensors="pt", add_special_tokens=False
        ).to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            use_cache=True,
            max_new_tokens=max_new_tokens,
        )

        output_text = self.tokenizer.decode(outputs[0])
        return self._postprocess_output(output_text)


# Emergency fix
class QuerySplitterOpenAI:

    def __init__(
        self,
        pretrained_model_name="gpt-3.5-turbo",
    ):

        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.pretrained_model_name = pretrained_model_name
        self.prompt_template = self._create_prompt_template()

    def split(self, query):
        prompt = self.prompt_template.format_prompt(query=query.strip()).to_string()
        messages = [
            {
                "role": "system",
                "content": "너는 문장을 '수업의 강의 주제과 관련된 문장', '수업의 평가와 관련된 문장'으로 분류하는 문장 분류 전문가야.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.pretrained_model_name,
            messages=messages,
        )
        output = response.choices[0].message.content

        return output

    def _create_prompt_template(self):
        template = """
    예시:

    질문:
    {example_query}

    답변:
    {example_answer}

    위의 형식과 동일한 형식으로 다음 질문에 대한 답변해주세요.

    질문:
    {query}

    답변:
    """
        example_query = "나는 인공지능과 관련된 수업을 듣고 싶은데, 빡세더라도 얻어가는게 많았으면 좋겠어. 수업 안에서 인공지능의 원론적인 내용보다는 딥러닝 관련 내용을 배우고싶고 교수님이 학점을 잘 주시고 강의력이 좋으면 좋겠어."
        example_answer = '{"주제관련": ["인공지능과 관련된 수업", "수업 안에서 인공지능의 원론적인 내용보다는 딥러닝 관련 내용을 배우는 수업"],\
    "평가관련": ["빡세더라도 얻어가는게 많은 수업", "교수님이 학점을 잘주시는 수업", "교수님이 강의력이 좋은 수업"]}'
        prompt_template = PromptTemplate(
            template=template,
            input_variables=["query"],
            partial_variables={
                "example_query": example_query,
                "example_answer": example_answer,
            },
        )
        return prompt_template
