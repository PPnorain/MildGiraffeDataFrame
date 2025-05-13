
URL="http://127.0.0.1:19008/"
PAGE_LIMIT=2000
GENERATION_SEED_LIMIT=100000
# GENERATION_SEED_LIMIT=100000
GENERATION_LARGE_STD=5000

GENERATE_METHOD=['请选择', 'FewShotGenerator', 'BatchGenerator']
# GENERATE_METHOD=['请选择', 'FewShotGenerator', 'BatchGenerator', 'ImitateGenerator', 'AbilityDirectGenerator']
PREPROCESS_METHOD=['请选择', 'pdf2markdown']
# SEARCH_METHOD=['请选择', 'keysearch']
SEARCH_METHOD_NEW=['请选择', 'key_search', 'regex_search', 'similar_search', 'cluster_search']
DUMPLICATE_METHOD=["Exact_Match", "MinHash"]
SIMILAR_METHOD=["Exact_Match", "difflib_distance", "levenshtein_distance", "embedding_cosine_similarity", "jaccard_distance", "ngram_similarity", "bleu_similarity", "rouge_similarity"]
