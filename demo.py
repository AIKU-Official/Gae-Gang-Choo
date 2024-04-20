import gradio as gr

from recsys import CourseRecommendationPipeline
from agent import ChatBot

recommender = CourseRecommendationPipeline(db_path="./vector_db")
print("Recommender initialized successfully")
bot = ChatBot(pretrained_model_name="gpt-4-0125-preview")
best_reviews = ""
NUM_RESULTS = 5  # align with the number of recommendations

with gr.Blocks() as app:

    query = gr.Textbox(label="Query")
    submit_button = gr.Button("개 강 추 👍")

    with gr.Row(visible=False) as output_row:

        with gr.Column() as agent_col:
            summary = gr.Textbox(label="Summary")
            with gr.Column() as chat_col:
                chatbot = gr.Chatbot(bubble_full_width=False)
                msg = gr.Textbox()
                clear = gr.ClearButton([msg, chatbot])

                def respond(message, chat_history):
                    bot_message = bot.chat(f"{best_course}", best_reviews, message)
                    chat_history.append((message, bot_message))
                    return "", chat_history

                msg.submit(respond, [msg, chatbot], [msg, chatbot])

        with gr.Column() as recommend_col:
            data_components = []
            tabs = [gr.Tab(str(i + 1)) for i in range(NUM_RESULTS)]

            for tab in tabs:
                with tab:
                    with gr.Row():
                        course_num_cls = gr.Textbox(label="학수번호/분반")
                    with gr.Row():
                        department = gr.Textbox(label="학과")
                        course_type = gr.Textbox(label="이수구분")
                    with gr.Row():
                        course_name = gr.Textbox(label="강의명")
                        instructor = gr.Textbox(label="교수자")
                        
                    with gr.Row():
                        timeslot = gr.Textbox(label="시간대")
                        room = gr.Textbox(label="강의실")
                    with gr.Accordion(label="강의 요목", open=False):
                        course_intro = gr.TextArea()
                    with gr.Accordion(label="선수 과목", open=False):
                        prerequisite = gr.Textbox(lines=3)
                    with gr.Accordion(label="강의게획서", open=False):
                        syllabus = gr.TextArea()
                    with gr.Accordion(label="관련 강의평"):
                        reviews = gr.Markdown()

                    data_components += [
                        tab,
                        course_num_cls,
                        department,
                        course_type,
                        course_name,
                        instructor,
                        timeslot,
                        room,
                        course_intro,
                        prerequisite,
                        syllabus,
                        reviews,
                    ]

    def on_submit(query):
        output = recommender.recommend(query)

        global best_course
        best_course = output[0]
        best_reviews = "\n".join(best_course["review"])
        bot.history = ""
        summarized_text = bot.summarize(
            info=best_course["info"], review=best_reviews, query=query
        )
        output_components = []
        for i in range(NUM_RESULTS):
            course_output = output[i]
            output_components += [
                gr.Tab(visible=True),
                gr.Textbox(f'{course_output["course_no"]}-{course_output["course_class"]}', label="학수번호/분반"),
                gr.Textbox(course_output["department"], label="학과"),
                gr.Textbox(course_output["course_type"], label="이수구분"),
                gr.Textbox(course_output["course_name"], label="강의명"),
                gr.Textbox(course_output["instructor"], label="교수자"),
                gr.Textbox(course_output["timeslot"], label="시간대"),
                gr.Textbox(course_output["room"], label="강의실"),
                gr.Textbox(course_output["course_intro"]),
                gr.Textbox(course_output["prerequisite"]),
                gr.Textbox(course_output["syllabus"]),
                gr.Markdown(
                    "\n___\n".join(course_output["review"]), label="관련 강의평"
                ),
            ]

        output_components.append(gr.Textbox(summarized_text, label="Summary"))
        output_components.append(gr.Row(visible=True))
        return output_components


    submit_button.click(
        fn=on_submit,
        inputs=[query],
        outputs=data_components + [summary, output_row],
    )


app.launch(share=True)
