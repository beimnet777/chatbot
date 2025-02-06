from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .data_loader import EMPLOYEE_DATA, FAISS_INDEX, TEXT_CHUNKS, CHUNK_TO_DEPARTMENT
from openai import OpenAI
from django.conf import settings






class ChatAPIView(APIView):
    # Initialize the OpenAI client

    client = OpenAI(
        api_key=settings.API_KEY
    )
    
    def retrieve_relevant_text(query, index, text_chunks, chunk_to_department, top_k=3):
        query_embedding = generate_embedding(query).reshape(1, -1)
        distances, indices = index.search(query_embedding, top_k)
        
        results = []
        for i in indices[0]:
            if i < len(text_chunks):  # Ensure index is within bounds
                chunk = text_chunks[i]
                department = chunk_to_department.get(i, "Unknown")  # Get department name
                results.append({"department": department, "text": chunk})

        return results  # Return structured data
        # return "\n".join(relevant_texts)
    
    def create_department_chunk_dict(results, separator=" ||| "):
        department_chunks = {}
        
        for result in results:
            dept = result.get("department", "Unknown")
            text = result.get("text", "")
            
            if dept in department_chunks:
                department_chunks[dept] += separator + text
            else:
                department_chunks[dept] = text

        return department_chunks
        
    # Create the system prompt
    def create_system_prompt(employee_data, department_data):
        system_prompt = (
            "You are New Age GPT, a virtual assistant for New Age company. Your responsibilities are:\n"
            "- Authenticate users based on their ID, and verify access to specific department data.\n"
            "- Understand natural user intents, including when users want to end the conversation with phrases like 'thanks,' 'all good,' 'bye,' 'no more help,' or similar.\n"
            "- If the user wants to end the conversation, respond politely and close the session.\n\n"
            "### Employee Data ###\n"
            f"{employee_data}\n\n"
            "### Department Data ###\n"
            f"{department_data}\n\n"
            "Respond naturally, concisely, and professionally at all times."
        )
        return [{"role": "system", "content": system_prompt}]

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
        
        close_results = retrieve_relevant_text(user_input, FAISS_INDEX, TEXT_CHUNKS, CHUNK_TO_DEPARTMENT, top_k=3)
        department_data = create_department_chunk_dict(close_results, separator=" ||| "):
        EMPLOYEE_DATA
        
        conversation = create_system_prompt(EMPLOYEE_DATA, department_data)
            
        
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
