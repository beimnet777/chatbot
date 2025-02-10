from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils.policy_loader import POLICY_TEXTS, POLICY_FILES, EMPLOYEE_DATA
from openai import OpenAI
from django.conf import settings



# print(EMPLOYEE_DATA, FAISS_INDEX, TEXT_CHUNKS, CHUNK_TO_DEPARTMENT)


class ChatAPIView(APIView):
    # Initialize the OpenAI client

    client = OpenAI(
        api_key=settings.API_KEY
    )
    
    def get_relevant_policies(self, contract_type, POLICY_TEXTS):
        """Fetches policies relevant to the contract type from memory."""
        relevant_policies = {}

        for policy_name, policy_text in POLICY_TEXTS.items():
            # Extract contract types from file name (e.g., "C1-C2" or "C1-C2-C3")
            policy_contracts = policy_name.replace(".pdf", "").replace(".docx", "").split("-")

            # Ensure contract type is allowed
            if contract_type.lower() in policy_contracts or "c1-c2-c3" in policy_contracts:
                relevant_policies[policy_name] = policy_text  # Fetch from memory

        return relevant_policies
    
    def validate_employee_id(self,employee_data, emp_id):
        """Check if Employee ID is valid and return contract type."""
        emp_id = str(emp_id)  # Ensure input Employee ID is treated as a string
        return employee_data.get(emp_id)
    
    
        
    # Create the system prompt
    def create_system_prompt(self):
        conversation_history = [
                                {"role": "system", "content": (
                                    "You are an AI assistant helping employees understand and access company policies.\n\n"
                                    "💡 **Key Rules for Responses:**\n"
                                    "1️⃣ Always provide concise and **structured summaries** of policies.\n"
                                    "2️⃣ If the user asks about a policy they have **access to**, summarize it **clearly** with actionable insights.\n"
                                    "3️⃣ If the user asks for more details, **progressively reveal** more information instead of declining the request.\n"
                                    "4️⃣ **DO NOT list all policies** unless the user explicitly asks for it.\n"
                                    "5️⃣ If a user asks for a policy **they do not have access to**, say:\n"
                                    "   ❌ 'This policy is restricted to [C1/C2/C3] employees.'\n"
                                    "6️⃣ If an employee asks, 'Can you send me the full policy document?', provide the download link if permitted.\n"
                                    "7️⃣ **Avoid repeating information** unnecessarily. Give relevant details only when needed.\n"
                                )}
                            ]
        return conversation_history

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
        try:
            user_input = request.data.get("message", "").strip()
            user_id = request.data.get("id", "").strip()
            contract_type = self.validate_employee_id(EMPLOYEE_DATA, user_id)
            print(EMPLOYEE_DATA, user_id, "***********88", request.data.get("id"))
            print(user_input)
            
            if not contract_type:
                return Response({
                    "response": "Invalid Employee Id"
                }, status=status.HTTP_200_OK)
            
            relevant_policies = self.get_relevant_policies(contract_type, POLICY_TEXTS)
            
            if not relevant_policies:
                return Response({
                    "response": f"❌ No policies found specifically for contract type: {contract_type}. However, some general company policies might still be applicable."
                }, status=status.HTTP_200_OK)
            
            # Try to find the most relevant policy
            requested_policy = None
            for policy_name in relevant_policies.keys():
                if any(word in policy_name.lower() for word in user_input.split()):
                    requested_policy = policy_name
                    break

            if not requested_policy and "policy" in user_input:
                return Response({
                    "response": "❌ You do not have access to this policy or it does not exist."
                }, status=status.HTTP_200_OK)
                
            
            
            
            conversation = self.create_system_prompt()
            conversation.append({"role": "user", "content": user_input})
                

            

            # Check if the user wants to end the conversation
            if self.detect_close_intent(conversation):
                print("I am here")
                return Response({
                    "response": "Goodbye! Feel free to return anytime you need assistance.",
                    "conversation": conversation,
                }, status=status.HTTP_200_OK)
            
            conversation.append({"role": "system", "content": str(relevant_policies[requested_policy])})

            # Generate a response
            response = self.generate_openai_response(conversation)

            # Append the assistant's response to the conversation
            conversation.append({"role": "assistant", "content": response})

            return Response({
                "response": response,
                "conversation": conversation,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
