from transformers import AutoTokenizer, AutoModel

cache_folder = "./models"
tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True, cache_dir=cache_folder)
model = AutoModel.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True, cache_dir=cache_folder).half().quantize(
    4).cuda()
response, history = model.chat(tokenizer, "你好", history=[])
print(response)
response, history = model.chat(tokenizer, "晚上睡不着应该怎么办", history=history)
print(response)
