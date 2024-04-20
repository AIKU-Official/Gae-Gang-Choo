from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI


class ChatBot:
    def __init__(
        self,
        pretrained_model_name="gpt-3.5-turbo",
    ):
        self.model = ChatOpenAI(
            model_name=pretrained_model_name, temperature=0.1, max_tokens=2048
        )
        self.history = ""

        self.template = """너는 수업 개요와 강의평이 주어지면 사용자의 요구사항에 맞게 질문에 답해주는 대화형 AI야.
        중요한 것은 주어진 대화내용과 수업 개요, 강의평만을 이용해서 답해야 한다는 것이고 주어진 수업 정보로 알 수 없는 내용을 물어본다면 솔직하게 모른다고 답해야해.

        수업 개요: {info}

        강의평: {review}

        대화 내용: {history}

        요구사항: {input}

        답변:
        """
        self.prompt = PromptTemplate(
            input_variables=["info", "review", "history", "input"],
            template=self.template,
        )

    def summarize(self, info, review, query):
        input = f"""조건: {query}
        수업 개요와 강의평을 요약해서 이 강의가 조건에 적합한 강의인지 알려주세요.
        조건에 대한 내용만 포함해서 요약하는 것이 중요합니다.
        """
        prompt_filled = self.prompt.format(
            info=info, review=review, history=self.history, input=input
        )

        ans = self.model.invoke(prompt_filled)

        new_interaction = f"Human: {input}\nAI: {ans.content}"
        self.history = f"{self.history}\n\n{new_interaction}"

        return ans.content

    def chat(self, info, review, query):
        prompt_filled = self.prompt.format(
            info=info, review=review, history=self.history, input=query
        )

        ans = self.model.invoke(prompt_filled)

        new_interaction = f"Human: {query}\nAI: {ans.content}"
        self.history = f"{self.history}\n\n{new_interaction}"

        return ans.content
