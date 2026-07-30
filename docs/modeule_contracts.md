# AI Module Contracts

## Summarizer

Input

```json
{
    "company_name": "",
    "chunk_id": "",
    "text": ""
}
```

Output

```json
{
    "company_name": "",
    "source_id": "",
    "chunk_id": "",
    "summary": "",
    "keywords": []
}
```

---

## Insight Extractor

Input

```json
{
    "summary": ""
}
```

Output

```json
{
    "background": "",
    "challenge": "",
    "strategy": "",
    "execution": "",
    "results": "",
    "learning": ""
}
```

---

## Generator

Input

Insights

Output

Final Case Study JSON