import argparse
import sys
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from collections import deque

parser = argparse.ArgumentParser()

parser.add_argument("--artifact-id", dest="artifact_id", type=str, help="artifactId анализируемого пакета")

parser.add_argument("--group-id", dest="group_id", type=str, help="groupId анализируемого пакета")
parser.add_argument("--version", dest="version", type=str, help="Версия пакета")

parser.add_argument("--test-repo", dest="test_repo", type=str, help="Путь к файлу тестового графа")

parser.add_argument("--output", dest="output", type=str, choices=['tree', 'list'], default='tree')
parser.add_argument("--exclude", dest="exclude", type=str, help="Подстрока для исключения")

args = parser.parse_args()

errors = []
if args.test_repo:
    if not args.artifact_id:
        errors.append("--artifact-id обязателен в тестовом режиме")
else:
    if not args.group_id or not args.artifact_id or not args.version:
        errors.append("В реальном режиме требуются: --group-id, --artifact-id, --version")

if errors:
    print("ошибка", file=sys.stderr)
    for e in errors:
        print(f" - {e}", file=sys.stderr)
    sys.exit(1)

if args.test_repo:
    print("анализ графа из файла")
    print(f"test_repo={args.test_repo}")
    if args.exclude:
        print(f"exclude={args.exclude}")
else:
    print("Параметры приложения:")
    print(f"group_id={args.group_id}")
    print(f"artifact_id={args.artifact_id}")
    print(f"version={args.version}")
    print(f"output={args.output}")
    print(f"exclude={args.exclude}")

def fetch_pom_from_maven(groupId, artifactId, version):
    if not version or '$' in version or version == '-':
        return None
    url = f"https://repo1.maven.org/maven2/{groupId.replace('.', '/')}/{artifactId}/{version}/{artifactId}-{version}.pom"
    try:
        with urlopen(url, timeout=5) as resp:
            return resp.read().decode('utf-8')
    except:
        return None

def extract_dependencies(pom_content):
    try:
        root = ET.fromstring(pom_content)
    except:
        return []
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    deps = []
    for dep in root.findall('.//m:dependency', ns):
        g_el = dep.find('m:groupId', ns)
        a_el = dep.find('m:artifactId', ns)
        v_el = dep.find('m:version', ns)

        g = g_el.text.strip() if g_el is not None and g_el.text else ""
        a = a_el.text.strip() if a_el is not None and a_el.text else ""
        v = v_el.text.strip() if v_el is not None and v_el.text else "-"

        if not g or not a or '$' in g or '$' in a or '$' in v:
            continue
        deps.append((g, a, v))
    return deps

def parse_test_graph(path):
    graph = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if parts:
                    node = parts[0]
                    children = parts[1:] if len(parts) > 1 else []
                    graph[node] = children
    except Exception as e:
        print(f"ошибка чтения {path}: {e}", file=sys.stderr)
        sys.exit(1)
    return graph


def build_graph_bfs(test_graph=None, start_artifact=None, start_group=None, start_version=None, exclude=None):
    if test_graph is not None:
        queue = deque([start_artifact])
        visited = set()
        graph = {}
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            if exclude and exclude in node:
                continue
            deps = test_graph.get(node, [])
            filtered = [d for d in deps if not (exclude and exclude in d)]
            graph[node] = filtered
            for d in filtered:
                if d not in visited:
                    queue.append(d)
        return graph
    else:
        start_key = (start_group, start_artifact, start_version)
        queue = deque([start_key])
        visited = set()
        graph = {}
        while queue:
            g, a, v = queue.popleft()
            key = (g, a, v)
            if key in visited:
                continue
            visited.add(key)
            full = f"{g}:{a}"
            if exclude and exclude in full:
                continue
            pom = fetch_pom_from_maven(g, a, v)
            if pom is None:
                graph[key] = []
                continue
            raw_deps = extract_dependencies(pom)
            filtered = []
            for dg, da, dv in raw_deps:
                dep_full = f"{dg}:{da}"
                if exclude and exclude in dep_full:
                    continue
                filtered.append((dg, da, dv))
            graph[key] = filtered
            for dep in filtered:
                dep_key = (dep[0], dep[1], dep[2])
                if dep_key not in visited:
                    queue.append(dep_key)
        return graph

def print_graph(graph, fmt='tree', test_mode=False):
    if test_mode:
        if fmt == 'tree':
            print("граф зависимостей (tree):")
            for node, deps in graph.items():
                print(f"{node}:")
                for d in deps:
                    print(f"  -> {d}")
        else:
            print("граф зависимостей (list):")
            s = set()
            for deps in graph.values():
                s.update(deps)
            for d in sorted(s):
                print(d)
    else:
        if fmt == 'tree':
            print("граф зависимостей (tree):")
            for (g, a, v), deps in graph.items():
                print(f"{g}:{a}:{v}:")
                for dg, da, dv in deps:
                    print(f"  -> {dg}:{da}:{dv}")
        else:
            print("граф зависимостей (list):")
            s = set()
            for deps in graph.values():
                for dg, da, dv in deps:
                    s.add(f"{dg}:{da}:{dv}")
            for line in sorted(s):
                print(line)

if args.test_repo:
    test_graph = parse_test_graph(args.test_repo)
    graph = build_graph_bfs(
        test_graph=test_graph,
        start_artifact=args.artifact_id,
        exclude=args.exclude
    )
    print_graph(graph, args.output, test_mode=True)
else:
    graph = build_graph_bfs(
        start_group=args.group_id,
        start_artifact=args.artifact_id,
        start_version=args.version,
        exclude=args.exclude
    )
    print_graph(graph, args.output, test_mode=False)
