from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .data_loader import CONVERSATION_PROMPT
from openai import OpenAI
from django.conf import settings






class ChatAPIView(APIView):
    # Initialize the OpenAI client
    print(CONVERSATION_PROMPT)
    client = OpenAI(
        api_key=settings.API_KEY
    )
    
    # Check for close intent with OpenAI
    def detect_close_intent(self,conversation):
        print("I am here detecting")
        try:
            close_prompt = conversation + [
                {"role": "user", "content": "Does the user want to end the conversation? Respond with 'yes' or 'no' only."}
            ]
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=close_prompt,
                max_tokens=3,
                temperature=0.0,
                store=True
            )
            intent_response = completion.choices[0].message.content.strip().lower()
            return intent_response == "yes"
        except Exception:
            return False

    # Generate a response using OpenAI
    def generate_openai_response(self,conversation):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                max_tokens=300,
                temperature=0.7,
                store=True
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"

    def post(self, request):
        user_input = request.data.get("message", "").strip()
        conversation = CONVERSATION_PROMPT
        
        print(user_input, "***********")

        # Append user input to the conversation
        conversation.append({"role": "user", "content": user_input})
        
        print(conversation, "***********")

        # Check if the user wants to end the conversation
        if self.detect_close_intent(conversation):
            print("I am here")
            return Response({
                "response": "Goodbye! Feel free to return anytime you need assistance.",
                "conversation": conversation,
            }, status=status.HTTP_200_OK)

        print(conversation, "***********&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        # Generate a response
        response = self.generate_openai_response(conversation)

        # Append the assistant's response to the conversation
        conversation.append({"role": "assistant", "content": response})

        return Response({
            "response": response,
            "conversation": conversation,
        }, status=status.HTTP_200_OK)
