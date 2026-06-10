"""
교차 검증 어댑터 패키지
========================
pharma_properties.py의 15개 메서드를 외부 독립 패키지와 교차 검증하기 위한
어댑터 모듈 모음.

각 어댑터는 통일된 인터페이스(dict 반환)를 제공하며,
해당 패키지가 미설치면 None을 반환합니다.

사용법
------
>>> from tests.cross_validators import biopython_adapter as bio
>>> result = bio.compute("AGCKNFFWKTFTSC")
>>> result["gravy"]  # float or None
"""
