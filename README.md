# 정지유 | 토스 Learner’s High 서버 3기 지원 포트폴리오

게시 사이트: https://jungjiyu.github.io/toss-learners-high/

- [모구시장 대표 글](https://jungjiyu.github.io/toss-learners-high/mogu/articles/retries.html)
- [모구시장 전체 아티클 11편](https://jungjiyu.github.io/toss-learners-high/mogu/index.html#articles)

## 원본과 게시 범위

모구시장 원본 저장소: https://github.com/jungjiyu/toss_mogu (비공개 유지)

게시 원본 커밋: `025c54c2fba77e0264351296ae0597bdff81dbdc`

`docs/portfolio/`의 안내·외부 글 11편과 실제 참조하는 자산·근거만 게시합니다. 내부 글, 작업 지시문, 전체 실험 디렉터리는 포함하지 않습니다. 원본이 비공개이므로 근거와 글에서 연결한 구현 코드는 로그인 없이 읽을 수 있는 사본으로 제공합니다. 구현 코드 두 파일의 개별 출처 커밋은 해당 페이지 및 `publication.json`에 기록했습니다.

원본 문서의 본문·SQL·반복별 수치·불리한 결과·한계는 유지하고 상대 링크만 배포 경로에 맞췄습니다. PG 검증 자료에는 원래부터 결제 키 해시와 합성 예약 식별자가 사용돼 있습니다. 시뮬레이터 식별자는 원장 대조를 위해 유지하며, 근거 파일의 로컬 사용자 디렉터리명은 `/Users/REDACTED`로 치환했습니다. 수정 파일·건수·출처 해시는 `publication.json`에서 확인할 수 있습니다.

## 갱신

```sh
python3 tools/publish_mogu.py /path/to/toss_mogu SOURCE_COMMIT
python3 tools/check_site.py
```

이 도구는 지정 커밋의 파일만 읽으며 다른 프로젝트 경로를 수정하지 않습니다. 게시 경로는 `mogu/`, 향후 프로젝트 경로는 `storybridge/`, `vlops/`입니다. 준비되지 않은 프로젝트는 사이트 목차에 표시하지 않습니다.

GitHub Pages 게시 소스: `main` 브랜치 루트(`/`), `.nojekyll` 사용.

공개 사이트 검수(Playwright와 Chrome 필요):

```sh
python3 tools/verify_live.py https://jungjiyu.github.io/toss-learners-high/
```

인증 없는 HTTP로 게시 파일의 해시를 대조하고, 쿠키가 없는 새 Chrome 컨텍스트에서 글·목록 이동과 데스크톱/390px 이미지·CSS·SQL·그래프·표를 검사합니다.
