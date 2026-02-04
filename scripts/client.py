import os
import time
from dotenv import load_dotenv
from openai import AzureOpenAI, RateLimitError, APIError

load_dotenv()

class LLMClient:
    def __init__(self, deployment_name: str = None):
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

    def generate_response(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.", temperature: float = 0.7) -> str:
        """
        Generates a response from the Azure OpenAI model with retry logic.
        """
        max_retries = 5
        current_temp = temperature
        
        for attempt in range(max_retries):
            try:
                # Detect if model is 'codex' or other completion-only models
                if "codex" in self.deployment_name.lower():
                    # Legacy Completions API
                    response = self.client.completions.create(
                        model=self.deployment_name,
                        prompt=f"{system_prompt}\n\nUser: {prompt}\nAssistant:",
                        temperature=current_temp,
                        max_tokens=1000
                    )
                    return response.choices[0].text.strip()
                else:
                    # Chat Completions API
                    response = self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=current_temp,
                        max_completion_tokens=1000
                    )
                    return response.choices[0].message.content
                    
            except RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5 # Increased backoff
                    print(f"⏳ Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            except APIError as e:
                # Handle Azure Content Filter (400)
                if e.code == 'content_filter' or (e.body and e.body.get('code') == 'content_filter'):
                    print(f"⚠️ Azure Content Filter triggered.")
                    return "Azure Content Filter triggered: The request was blocked due to safety policies."
                
                # Handle Unsupported Temperature (400)
                if "temperature" in str(e).lower() and "unsupported" in str(e).lower():
                    print(f"⚠️  Model {self.deployment_name} requires default temperature. Retrying with temperature=1...")
                    current_temp = 1.0
                    continue # Retry immediately with new temp
                
                # Handle Codex Operation Not Supported -> Try Chat Fallback
                if "operation does not work" in str(e).lower() and "codex" in self.deployment_name.lower():
                     print(f"⚠️  Completions API failed for {self.deployment_name}. Retrying with Chat API...")
                     try:
                        response = self.client.chat.completions.create(
                            model=self.deployment_name,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=current_temp,
                            max_completion_tokens=1000
                        )
                        return response.choices[0].message.content
                     except Exception as e2:
                         print(f"❌ Fallback failed: {e2}")
                         raise e

                print(f"Error calling LLM: {e}")
                raise
            except Exception as e:
                print(f"Error calling LLM: {e}")
                raise
        return ""
