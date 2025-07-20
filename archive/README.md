# 📁 Archive Directory

이 폴더는 더 이상 사용하지 않는 코드들을 보관하는 곳입니다.

## 🗂️ **보관된 코드들**

### **google_search_api/** 
- **보관 날짜**: 2025-07-13
- **보관 이유**: `google_searcher`로 대체됨 (웹 스크래핑 방식이 더 효과적)
- **포함 파일**:
  - `google_search_api/` - Google Custom Search API 도구
  - `google_search_api.py` - Google Search API 노드
- **대체 기능**: `GoogleSearcherNode` (src/graph/nodes/google_searcher.py)

### **pipelines/**
- **googlesearch_pipeline.py** - Google Search API 파이프라인 (대체: google_searcher_pipeline.py)

## 🔄 **복원 방법**

필요시 아래 명령어로 복원할 수 있습니다:

```bash
# Google Search API 복원
cp -r archive/google_search_api/ src/tools/
cp archive/google_search_api/google_search_api.py src/graph/nodes/
cp archive/pipelines/googlesearch_pipeline.py pipelines/

# import 문 복원 (수동으로 __init__.py 파일들 수정 필요)
```

## 📋 **아카이빙 기록**

| 날짜 | 항목 | 이유 | 대체 기능 |
|------|------|------|----------|
| 2025-07-13 | Google Search API | 웹 스크래핑 방식으로 대체 | GoogleSearcherNode |