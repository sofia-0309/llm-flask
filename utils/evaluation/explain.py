from utils.evaluation.llm_api import call_openai_for_evaluation
from jinja2 import Template
import os
from config import supabase_client


class Explanation:
    def __init__(self, data):
        self.task_type = data['task_type']
        self.question = data["question"]
        self.selection = data["selection"]
        self.is_correct = data["is_correct"]
        self.option_a = data["option_a"]
        self.option_b = data["option_b"]
        self.option_c = data["option_c"]
        self.option_d = data["option_d"]
        self.client = supabase_client
        self.quiz_id = data["quiz_id"]
        self.user_id = data["user_id"]
        self.message = data["message"]
    def construct(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))  

        prompt_path = os.path.join(ROOT_DIR, "prompts", "evaluation", "explain.txt")

        with open(prompt_path, "r") as file:
            prompt_str = file.read()
            full_prompt = Template(prompt_str)
        return full_prompt.render( question=self.question,option_a = self.option_a, option_b = self.option_b, option_c = self.option_c, option_d = self.option_d, selection=self.selection, is_correct = self.is_correct)
    def generate_answer(self):
        if self.task_type == "explain":
            prompt = self.construct()

            print(type(self.quiz_id))
            print(type(self.user_id))
            print(self.user_id)
            print(self.quiz_id)
            text = call_openai_for_evaluation(prompt = prompt)

            def save_conversation(prompt, ai_response):
                
                existing_conv = (
                    self.client.table("conversations")
                    .select("conversation_id")
                    .eq("user_id", self.user_id)
                    .eq("quiz_id", self.quiz_id)
                    .execute()
                )

                if not existing_conv.data:
                    conversation = (
                        self.client.table("conversations")
                        .insert({
                            "user_id": self.user_id,
                            "quiz_id": self.quiz_id,
                        })
                        .execute()
                    )
                    conversation_id = conversation.data[0]["conversation_id"]

                else:
                    conversation_id = existing_conv.data[0]["conversation_id"]

                self.client.table("messages").insert({
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": prompt,
                    "is_shown": False
                }).execute()

                self.client.table("messages").insert({
                    "conversation_id": conversation_id,
                    "role": "expert",
                    "content": ai_response,
                    "is_shown": True
                }).execute()

            save_conversation(prompt, text["output"]["content"])

        elif self.task_type == "follow":

            existing_conv = (
                self.client.table("conversations")
                .select("conversation_id")
                .eq("user_id", self.user_id)
                .eq("quiz_id", self.quiz_id)
                .execute()
            )

            def save_conversation(prompt, ai_response):
                    existing_conv = (
                        self.client.table("conversations")
                        .select("conversation_id")
                        .eq("user_id", self.user_id)
                        .eq("quiz_id", self.quiz_id)
                        .execute()
                    )

                    if not existing_conv.data:
                        conversation = (
                            self.client.table("conversations")
                            .insert({
                                "user_id": self.user_id,
                                "quiz_id": self.quiz_id,
                            })
                            .execute()
                        )
                        conversation_id = conversation.data[0]["conversation_id"]

                    else:
                        conversation_id = existing_conv.data[0]["conversation_id"]

                    self.client.table("messages").insert({
                        "conversation_id": conversation_id,
                        "role": "user",
                        "content": prompt,
                        "is_shown": True
                    }).execute()

                    self.client.table("messages").insert({
                        "conversation_id": conversation_id,
                        "role": "expert",
                        "content": ai_response,
                        "is_shown": True
                    }).execute()




            if existing_conv.data:
                conversation_id = existing_conv.data[0]["conversation_id"]

                messages_query = (
                self.client.table("messages") 
                .select("*") 
                .eq("conversation_id", conversation_id) 
                .order("created_at", desc=False) 
                .execute()
                )

                conversation_history = [
                    {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
                    for m in messages_query.data
                ]

                conversation_history.append({"role": "user", "content": self.message})
                print("user_message:" ,self.message)

                text = call_openai_for_evaluation(conversation_history = conversation_history)

                



                print(text)
            else:
                text = call_openai_for_evaluation(prompt=self.message)

            save_conversation(self.message, text["output"]["content"])

                
        return text
        

    
