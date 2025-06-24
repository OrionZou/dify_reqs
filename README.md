# 快速使用

### 配置环境

```bash
uv venv .venv -p 3.11
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

### 离线运行示例

默认是使用 demo_data/output.xlsx 数据。参数：xlsx 文件路径，高意向评论条数。

```bash
PYTHONPATH=$PYTHONPATH:. python3 app/offline_main.py
```

### web server 

调试模式
```bash
uvicorn app.server:app --reload
```
正式启动
```bash
uvicorn app.server:app --host 0.0.0.0 --port 8711
```

请求 demo
```bash
python exps/req_high_comments_demo.py
```



# 接口文档：获取高意向评论

## 接口地址
`POST /get_high_intent_comments`

## 接口描述
该接口用于根据视频信息和评论列表，筛选出高意向评论。用户可以指定希望返回的高意向评论数量。

---

## 请求参数

### 请求头
| 参数名          | 类型   | 必填 | 描述                 |
|-----------------|--------|------|----------------------|
| Content-Type    | string | 是   | 请求体的内容类型，必须为 `application/json` |

### 请求体
请求体为 JSON 格式，包含以下字段：

| 参数名                  | 类型       | 必填 | 描述                                                                 |
|-------------------------|------------|------|----------------------------------------------------------------------|
| vedio_info              | string     | 是   | 视频的相关信息，包含行业和关键字等描述信息。                          |
| comment_list            | array(dict) | 是   | 评论列表，每条评论为一个字典，包含评论的详细信息。                     |
| high_intent_comment_num | integer    | 否   | 希望返回的高意向评论数量，默认为 5，必须大于 0。                      |

#### `vedio_info` 示例
```json
"行业: 教育 关键字: 在线学习"
```

#### `comment_list` 示例
`comment_list` 是一个包含评论的数组，每条评论的字段如下：

| 字段名          | 类型   | 必填 | 描述                 |
|-----------------|--------|------|----------------------|
| comment_content | string | 是   | 评论内容             |
| comment_time    | string | 否   | 评论发布时间         |
| ip_address      | string | 否   | 评论发布者的 IP 属地 |
| response_count  | int    | 否   | 评论的回复数         |
| like_count      | int    | 否   | 评论的点赞数         |
| uid             | string | 是   | 评论的唯一标识 UID 8~64 位   |

##### 示例
```json
[
    {
        "comment_content": "这门课程真的很棒！",
        "comment_time": "2023-10-01 12:00:00",
        "ip_address": "北京",
        "response_count": 10,
        "like_count": 50,
        "uid": "12345"
    },
    {
        "comment_content": "希望能有更多类似的课程。",
        "comment_time": "2023-10-02 14:30:00",
        "ip_address": "上海",
        "response_count": 5,
        "like_count": 20,
        "uid": "67890"
    }
]
```

#### 完整请求体示例
```json
{
    "vedio_info": "行业: 教育 关键字: 在线学习",
    "comment_list": [
        {
            "comment_content": "这门课程真的很棒！",
            "comment_time": "2023-10-01 12:00:00",
            "ip_address": "北京",
            "response_count": 10,
            "like_count": 50,
            "uid": "12345"
        },
        {
            "comment_content": "希望能有更多类似的课程。",
            "comment_time": "2023-10-02 14:30:00",
            "ip_address": "上海",
            "response_count": 5,
            "like_count": 20,
            "uid": "67890"
        }
    ],
    "high_intent_comment_num": 5
}
```

---

## 响应参数

### 响应体
响应体为 JSON 格式，返回一个高意向评论的列表，每条评论包含以下字段与请求相同。

---

## 错误码

| 状态码 | 描述                     |
|--------|--------------------------|
| 200    | 请求成功，返回高意向评论 |
| 400    | 请求参数错误             |
| 500    | 服务器内部错误           |

---

## 示例

### 请求示例
```bash
curl -X POST http://127.0.0.1:8000/get_high_intent_comments \
-H "Content-Type: application/json" \
-d '{
    "vedio_info": "行业: 教育 关键字: 在线学习",
    "comment_list": [
        {
            "comment_content": "这门课程真的很棒！",
            "comment_time": "2023-10-01 12:00:00",
            "ip_address": "北京",
            "response_count": 10,
            "like_count": 50,
            "uid": "12322345"
        },
        {
            "comment_content": "希望能有更多类似的课程。",
            "comment_time": "2023-10-02 14:30:00",
            "ip_address": "上海",
            "response_count": 5,
            "like_count": 20,
            "uid": "673123890"
        },
        {
            "comment_content": "希望能有更11多类似的课程。",
            "comment_time": "2023-10-02 14:30:00",
            "ip_address": "上海",
            "response_count": 5,
            "like_count": 20,
            "uid": "67812390"
        }
    ],
    "high_intent_comment_num": 5
}'
```

### 响应示例
```json
[{
    "comment_content": "希望能有更多类似的课程。",
    "uid": "673123890",
    "user_name": null,
    "comment_time": "2023-10-02T14:30:00",
    "ip_address": "上海",
    "response_count": 5,
    "like_count": 20
}]

```

---

以上是接口的详细文档，涵盖了输入、输出及示例，便于开发和测试使用。
