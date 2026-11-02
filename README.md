# 정지유 | 토스 Learner’s High 서버 3기 지원 포트폴리오

게시 사이트: https://jungjiyu.github.io/toss-learners-high/

- [모구시장 대표 글](https://jungjiyu.github.io/toss-learners-high/mogu/articles/retries.html)
- [모구시장 전체 아티클 11편](https://jungjiyu.github.io/toss-learners-high/mogu/index.html#articles)
- [StoryBridge 대표 글 — 같은 메시지가 일부 수신자에게만 늦었던 이유](https://jungjiyu.github.io/toss-learners-high/storybridge/articles/reconnect.html)
- [StoryBridge 전체 아티클 11편](https://jungjiyu.github.io/toss-learners-high/storybridge/index.html#all)

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

## StoryBridge 원본과 갱신

원본 저장소: `jungjiyu/toss_storybridge` (비공개 유지).
게시 원본 커밋: `79c3da3aae9ba09db24ff334b172039fe2c7fa38`.
검토 기준 `c07dc77` 이후 조건부 backlog 증가량, SEND 미확정과 복구 실패 회차, 시험별 전체/수신자별 p99의 세 문장만 교정했다.

`/storybridge/`에는 안내와 외부 아티클 11편, 승인된 아키텍처, 실제 링크가 참조하는 자산·측정·진단 자료를 게시한다. 비공개 저장소 링크는 공개용 사본으로 변경했으며, 내부 아티클 링크는 해당 글의 측정·구현 근거 목록으로 연결한다. 표·SQL·실험 수치·실패 결과는 유지한다.

구현 코드는 각각의 검증 커밋에서 추출한다.

- 기준 구현: `91ce2a72a9635a60d8171db5ab5840ade3692926`
- 최종 단일 서버: `d1ab45300a25fc763381899466752482bf6e0921`
- 별도 RabbitMQ 다중 gateway: `c85d5345e1effcc73cf4816341217ad1ad1e7868`

게시 파일의 출처·해시·링크 변환과 민감값 치환 내역은 `storybridge-publication.json`에 기록한다. 합성 사용자·방·메시지 식별자는 원장 대조를 위해 유지하고, 로컬 사용자 디렉터리명과 자격정보는 공개 사본에서 제거한다. 원본 저장소나 기존 `mogu/`는 게시 도구가 수정하지 않는다.

게시본에서는 404였던 Jakarta WebSocket 2.1 `RemoteEndpoint` 링크를 올바른 API 주소로 수정했고, HTTP403을 반환하던 MySQL8.4 참고 링크 두 곳은 같은 버전의 Oracle 공식 매뉴얼로 연결했다. 원본 아티클의 기술 설명이나 측정값은 바꾸지 않았다.

```sh
# 원본에서 문서 재생성·검수·커밋한 후 그 정확한 SHA를 지정한다.
python -X utf8 tools/publish_storybridge.py /path/to/toss_storybridge SOURCE_COMMIT
python -X utf8 tools/check_site.py
python -X utf8 tools/verify_storybridge_live.py https://jungjiyu.github.io/toss-learners-high/
```

공개 검수에는 `playwright`와 설치된 Chrome을 사용한다(`python -m pip install playwright`). 브라우저는 쿠키·로그인 정보가 없는 새 컨텍스트로 연다. Pages는 기존과 같이 `main` 루트를 게시하며 `/mogu/` 주소는 유지한다.

두 프로젝트의 안내 페이지는 SVG 크기를 HTML의 width/height에도 지정한다. 처음 접속할 때 이미지 로딩으로 `#all`·`#articles` 위치가 밀리는 것을 막기 위한 게시 처리이며 원본 그림·본문은 그대로다. `tools/check_storybridge_anchor.py <공개 URL>`로 데스크톱·390px의 새 브라우저 컨텍스트를 각각 3회 열어 실제 목록 위치를 확인한다.

공개 검수 결과는 [verification/storybridge-publication.json](verification/storybridge-publication.json)에 기록했다. 검수한 콘텐츠 커밋, 원본 커밋, HTTP 상태·내용 해시, 브라우저 이동과 실제 화면 검수 범위를 포함한다.
