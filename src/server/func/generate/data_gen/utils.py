import os, json, time, httpx, requests, asyncio, aiohttp

def load_jsonl(file_path):
    dat = open(file_path, 'r').readlines()
    dat = [json.loads(i) for i in dat]
    return dat


def save_jsonl(sample_ls, save_path):
    with open(save_path, 'w', encoding='utf-8') as f:
        for ipt in sample_ls:
            json_str = json.dumps(ipt, ensure_ascii=False)
            f.write(json_str + '\n')


def clean_patterns(txt, patterns):
    for pattern in patterns:
        txt = txt.replace(pattern, '')
    return txt

class RequestAI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url + "chat/completions"
        self.headers = {"Content-Type": 'application/json'}

def get_gpt4_response(query, client, chat_config, sleep_time):
    '''
    功能简介：请求方式优化，可以采用OpenAI和Request方式请求。
    '''
    try:
        if isinstance(client, RequestAI):
            json_data = dict(
                model=chat_config['model'],
                messages=[
                    {"role": "user", "content": query}
                ],
                temperature=chat_config['temperature'],
                top_p=chat_config['top_p'],
            )
            response = requests.post(client.base_url, headers=client.headers, json=json_data, timeout=60)
        else:
            response = client.chat.completions.create(
                model=chat_config['model'],
                messages=[
                    {"role": "user", "content": query}
                ],
                temperature=chat_config['temperature'],
                top_p=chat_config['top_p'],
                # timeout=20
                # presence_penalty=0.5,
                # frequency_penalty=0.2,
            )
    except Exception as e:
        return {'code': 500, 'data':query, 'message':f'API访问失败【{e}】'}
    try:
        if isinstance(client, RequestAI):
            response = response.json()["choices"][0]["message"]["content"]
        else:
            response = response.choices[0].message.content
    except Exception as e:
        return {'code': 501, 'data':query, 'message':f'API数据获取失败【{e}】'}
    time.sleep(sleep_time)
    return response

# async def get_gpt4_response(query, client, chat_config, sleep_time):
#     '''
#     功能简介：请求方式优化，可以采用OpenAI和Request方式请求。
#     '''
#     try:
#         if isinstance(client, RequestAI):
#             json_data = dict(
#                 model=chat_config['model'],
#                 messages=[
#                     {"role": "user", "content": query}
#                 ],
#                 temperature=chat_config['temperature'],
#                 top_p=chat_config['top_p'],
#             )
#             # async with aiohttp.ClientSession() as session:
#             #     async with session.post(client.base_url, headers=client.headers, json=json_data, timeout=60) as response:
#             #         response_json = await response.json()
#             async with httpx.AsyncClient() as cli:
#                 response = await cli.post(client.base_url, headers=client.headers, json=json_data, timeout=60)
#         else:
#             response = await client.chat.completions.create(
#                 model=chat_config['model'],
#                 messages=[
#                     {"role": "user", "content": query}
#                 ],
#                 temperature=chat_config['temperature'],
#                 top_p=chat_config['top_p'],
#                 # timeout=20
#                 # presence_penalty=0.5,
#                 # frequency_penalty=0.2,
#             )
#     except Exception as e:
#         return {'code': 500, 'data': query, 'message': f'API访问失败【{e}】'}

#     try:
#         if isinstance(client, RequestAI):
#             response_text = response_json["choices"][0]["message"]["content"]
#         else:
#             response_text = response.choices[0].message.content
#     except Exception as e:
#         return {'code': 501, 'data': query, 'message': f'API数据获取失败【{e}】'}

#     await asyncio.sleep(sleep_time)
#     return response_text

def load_openai_client(config):
    if config['api_type'] == 'azure':
        from openai import AzureOpenAI
        client = AzureOpenAI(api_key=config['api_key'], azure_endpoint=config['api_base'], api_version="2023-05-15")
    elif config['api_type'] == 'openai':
        from openai import OpenAI
        client = OpenAI(api_key=config['api_key'], base_url=config['api_base'])
    else:
        client = RequestAI(api_key=config['api_key'], base_url=config['api_base'])
    return client

def heart_beat(interval, dbobj):
    heart = 0
    while True:
        # from ipdb import set_trace
        # set_trace()
        dbobj.db_add_heart(heart)
        time.sleep(interval)
        heart += 1