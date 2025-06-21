from gemini_api import GeminiAPI

llm = GeminiAPI(model_name="gemini-2.0-flash")      # 可改 2.5-pro / flash
# resp = llm(
#     messages=[{"role":"user","content":"用中文回答：2+2?"}],
#     temperature=0.0
# )
# print(resp["choices"][0]["message"]["content"])

reply = llm([{"role": "user", "content": "用中文回答：2+2=?"}],
            temperature=0.0)

print("API 直接回傳：", reply["choices"][0]["message"]["content"])
print("從 llm.response 讀：", llm.response["choices"][0]["message"]["content"])
