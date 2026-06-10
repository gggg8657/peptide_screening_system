"""pipeline_local 패키지를 직접 실행할 때 run_pipeline_local을 호출한다.

사용법:
    python -m pipeline_local           # 이 파일 실행
    python -m pipeline_local.run_pipeline_local  # 동일
"""
from pipeline_local.run_pipeline_local import main

main()
