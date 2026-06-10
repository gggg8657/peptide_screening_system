"""Linear → Obsidian 동기화 스크립트

사용법:
  python3 scripts/sync_linear_to_obsidian.py                    # 전체 이슈
  python3 scripts/sync_linear_to_obsidian.py --project "AI Co-Scientist for 방사선의약품"  # 프로젝트 필터
  python3 scripts/sync_linear_to_obsidian.py --label MeetAction  # 라벨 필터
"""
import json, urllib.request, os, sys, argparse

API_KEY = os.environ.get("LINEAR_API_KEY", "")
if not API_KEY:
    sys.exit("환경변수 LINEAR_API_KEY 를 설정하세요 (export LINEAR_API_KEY=lin_api_...)")
TEAM_ID = os.environ.get("LINEAR_TEAM_ID", "5185a833-55c6-4888-a9a9-d271d37dbc4a")
VAULT_DIR = os.path.expanduser("~/Documents/ObsidianVault")
SYNC_DIR = os.path.join(VAULT_DIR, "Linear Issues")


def fetch_issues(project_filter=None, label_filter=None):
    """Linear GraphQL로 이슈 가져오기"""
    query = """
    {
      team(id: "%s") {
        issues(first: 200, orderBy: updatedAt) {
          nodes {
            identifier title description
            state { name }
            assignee { name }
            priority priorityLabel
            project { name }
            labels { nodes { name } }
            url createdAt updatedAt
          }
        }
      }
    }
    """ % TEAM_ID

    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json", "Authorization": API_KEY}
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    issues = data["data"]["team"]["issues"]["nodes"]

    # Linear 온보딩/튜토리얼 이슈 제외
    ONBOARDING_KEYWORDS = [
        "welcome to linear", "invite your teammates", "customize settings",
        "connect github", "connect to slack", "use cycles", "use projects",
        "navigate linear", "next steps",
    ]
    issues = [
        i for i in issues
        if not any(kw in i["title"].lower() for kw in ONBOARDING_KEYWORDS)
        and i["title"].lower() != "hello"
    ]

    # 필터링
    if project_filter:
        issues = [i for i in issues if i.get("project") and project_filter.lower() in i["project"]["name"].lower()]
    if label_filter:
        issues = [i for i in issues if any(label_filter.lower() in l["name"].lower() for l in i["labels"]["nodes"])]

    return issues


def write_issue_md(issue, output_dir, all_identifiers=None):
    """이슈를 마크다운 파일로 저장"""
    all_identifiers = all_identifiers or set()
    identifier = issue["identifier"]
    title = issue["title"]
    status = issue["state"]["name"]
    assignee = issue["assignee"]["name"] if issue["assignee"] else "Unassigned"
    priority = issue["priorityLabel"]
    project = issue["project"]["name"] if issue["project"] else "None"
    labels = ", ".join(l["name"] for l in issue["labels"]["nodes"]) or "None"
    desc = issue["description"] or ""
    url = issue["url"]
    created = issue["createdAt"][:10]
    updated = issue["updatedAt"][:10]

    # Obsidian 태그 생성 (그래프 뷰에서 연결)
    tags = []
    tags.append(f"linear/{status.lower().replace(' ', '-')}")
    tags.append(f"project/{project.lower().replace(' ', '-').replace('/', '-')}" if project != "None" else "project/unassigned")
    tags.append(f"priority/{priority.lower()}")
    for lbl in issue["labels"]["nodes"]:
        tags.append(f"label/{lbl['name'].lower().replace(' ', '-')}")
    if assignee != "Unassigned":
        tags.append(f"assignee/{assignee.lower().replace(' ', '-')}")

    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    tags_inline = " ".join(f"#{t.replace('/', '_')}" for t in tags)

    # 주제 허브 링크
    topics = get_topics(issue)
    topic_links = " ".join(f"[[{t}]]" for t in topics) if topics else ""

    # 본문 내 CHA-xxx → 위키링크 변환
    desc = add_wikilinks(desc, identifier, all_identifiers)

    content = f"""---
linear_id: {identifier}
linear_status: {status}
linear_assignee: {assignee}
linear_priority: {priority}
linear_project: {project}
linear_labels: [{labels}]
linear_url: {url}
created: {created}
updated: {updated}
tags:
{tags_yaml}
---

# {identifier}: {title}

{tags_inline}

**Status**: {status} | **Assignee**: {assignee} | **Priority**: {priority}
**Project**: {project} | **Labels**: {labels}
**Created**: {created} | **Updated**: {updated}
**Linear**: [{identifier}]({url})
**Topics**: {topic_links if topic_links else "—"}

---

{desc}
"""

    filename = f"{identifier} {title[:50].replace('/', '-').replace(':', '-')}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return identifier, title


TOPIC_KEYWORDS = {
    "FWKT 약리단": ["fwkt", "pharmacophore", "약리단"],
    "FlexPepDock 도킹": ["flexpep", "docking", "dock", "도킹", "ddg", "rosetta"],
    "SSTR 선택성": ["sstr1", "sstr2", "sstr3", "sstr4", "sstr5", "selectivity", "선택성"],
    "pepADMET": ["pepadmet", "admet", "admetlab", "독성"],
    "Stability 안정성": ["stability", "half-life", "serum", "protease", "안정성", "반감기"],
    "Mutation 변이": ["mutation", "mutant", "blosum", "thompson", "변이", "후보 생성"],
    "Scoring 스코어링": ["scoring", "pareto", "gnina", "bayesian", "ecr", "스코어"],
    "UI 대시보드": ["dashboard", "frontend", "panel", "ui", "대시보드", "react"],
    "Infra 인프라": ["conda", "gpu", "ci/cd", "github actions", "인프라"],
    "Paper 논문": ["paper", "manuscript", "논문", "kns", "abstract"],
}


def get_topics(issue):
    """이슈가 속하는 주제 목록 반환"""
    text = ((issue.get("title") or "") + " " + (issue.get("description") or "")).lower()
    return [topic for topic, kws in TOPIC_KEYWORDS.items() if any(kw in text for kw in kws)]


def add_wikilinks(desc, identifier, all_identifiers):
    """본문에서 CHA-xxx 패턴을 [[CHA-xxx ...]] 위키링크로 변환"""
    import re
    for other_id in all_identifiers:
        if other_id != identifier and other_id in (desc or ""):
            desc = desc.replace(other_id, f"[[{other_id}]]")
    return desc


def generate_topic_hubs(issues, output_dir):
    """주제별 허브 노트 생성 — 그래프 뷰에서 이슈들을 연결하는 중심 노드"""
    from collections import defaultdict
    topic_issues = defaultdict(list)

    for issue in issues:
        for topic in get_topics(issue):
            topic_issues[topic].append(issue)

    hub_dir = os.path.join(output_dir, "_Topics")
    os.makedirs(hub_dir, exist_ok=True)

    for topic, topic_list in topic_issues.items():
        # 상태별 분류
        by_status = defaultdict(list)
        for i in topic_list:
            by_status[i["state"]["name"]].append(i)

        links = ""
        for status in ["In Progress", "Todo", "Backlog", "Done", "Duplicate", "Cancelled"]:
            items = by_status.get(status, [])
            if items:
                links += f"\n### {status} ({len(items)})\n"
                for i in items:
                    ident = i["identifier"]
                    title = i["title"][:60]
                    project = i["project"]["name"] if i.get("project") else "-"
                    links += f"- [[{ident}]] {title} `{project}`\n"

        content = f"""---
type: topic-hub
topic: {topic}
issue_count: {len(topic_list)}
---

# {topic}

> 이 노트는 자동 생성된 주제 허브입니다. 관련 Linear 이슈를 연결합니다.

**관련 이슈**: {len(topic_list)}개
{links}
"""
        filepath = os.path.join(hub_dir, f"{topic}.md")
        with open(filepath, "w") as f:
            f.write(content)

    return len(topic_issues)


def main():
    parser = argparse.ArgumentParser(description="Linear → Obsidian 동기화")
    parser.add_argument("--project", help="프로젝트 이름 필터 (부분 일치)")
    parser.add_argument("--label", help="라벨 필터 (부분 일치)")
    parser.add_argument("--output", help="출력 디렉토리 (기본: vault/Linear Issues)")
    parser.add_argument("--flat", action="store_true", help="프로젝트별 하위 폴더 없이 flat 구조")
    args = parser.parse_args()

    base_dir = args.output or SYNC_DIR
    os.makedirs(base_dir, exist_ok=True)

    print(f"Linear 이슈 동기화 시작...")
    if args.project:
        print(f"  프로젝트 필터: {args.project}")
    if args.label:
        print(f"  라벨 필터: {args.label}")

    issues = fetch_issues(project_filter=args.project, label_filter=args.label)
    print(f"  {len(issues)}개 이슈 가져옴")

    all_identifiers = {i["identifier"] for i in issues}

    project_counts = {}
    for issue in issues:
        project_name = issue["project"]["name"] if issue["project"] else "_Unassigned"

        if args.flat:
            output_dir = base_dir
        else:
            # 프로젝트별 하위 디렉토리
            safe_name = project_name.replace("/", "-").replace(":", "-")
            output_dir = os.path.join(base_dir, safe_name)
            os.makedirs(output_dir, exist_ok=True)

        identifier, title = write_issue_md(issue, output_dir, all_identifiers)
        status = issue["state"]["name"]
        print(f"  ✅ {identifier} [{project_name[:30]}] [{status}] {title[:50]}")
        project_counts[project_name] = project_counts.get(project_name, 0) + 1

    # 주제 허브 노트 생성
    n_topics = generate_topic_hubs(issues, base_dir)

    print(f"\n동기화 완료: {base_dir} ({len(issues)}개 이슈, {n_topics}개 주제 허브)")
    print(f"프로젝트별:")
    for pname, cnt in sorted(project_counts.items(), key=lambda x: -x[1]):
        print(f"  {cnt:3d}개  {pname}")


if __name__ == "__main__":
    main()
