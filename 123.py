import argparse
import sys
import xml.etree.ElementTree as ET
import os
from urllib.request import urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--package", dest="packagename", type=str, help="Имя анализируемого пакета")
parser.add_argument("--url", dest="url", type=str, help="URL адрес репозитория или путь к файлу тестового репозитория")
parser.add_argument("--mode", dest="mode", type=str, choices=['local', 'remote'], default='remote',
                    help="Режим работы с тестовым репозиторием: local или remote")
parser.add_argument("--version", dest="version", type=str, help="Версия пакета (например, 1.2.3)")
parser.add_argument("--output", dest="output", type=str, choices=['tree', 'list'], default='tree',
                    help="Режим вывода зависимостей: 'tree' или 'list'")
parser.add_argument("--filter", dest="filter", type=str, help="Подстрока для фильтрации пакетов")

args = parser.parse_args()

errors = []
if not args.packagename:
    errors.append("Имя пакета (--package) обязательно")
if not args.url:
    errors.append("URL (--url) обязателен")
if args.version and not args.version.replace('.', '').isdigit():
    errors.append("Версия пакета (--version) должна быть в формате x.y.z")
if args.mode not in ['local', 'remote']:
    errors.append("--mode должно быть local или remote")
if args.output not in ['tree', 'list']:
    errors.append("--output должно быть tree или list")

if errors:
    print("ошибка ", file=sys.stderr)
    for e in errors:
        print(f" - {e}", file=sys.stderr)
    sys.exit(1)

print("Параметры приложения:")
print(f"packagename={args.packagename}")
print(f"url={args.url}")
print(f"mode={args.mode}")
print(f"version={args.version}")
print(f"output={args.output}")
print(f"filter={args.filter}")

def get_pom_content(url, mode):
    if mode == 'local':
        with open(url, 'r', encoding='utf-8') as f:
            return f.read()
    elif mode == 'remote':
        response = urlopen(url)
        return response.read().decode('utf-8')

def extract_dependencies(pom_content):
    root = ET.fromstring(pom_content)
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    deps = []
    for dep in root.findall('.//m:dependency', ns):
        groupId = dep.find('m:groupId', ns)
        artifactId = dep.find('m:artifactId', ns)
        version = dep.find('m:version', ns)

        if groupId is not None and artifactId is not None:
            groupId_text = groupId.text
            artifactId_text = artifactId.text
            version_text = version.text if version is not None else 'N/A'
            deps.append((groupId_text, artifactId_text, version_text))
    return deps

try:
    pom_content = get_pom_content(args.url, args.mode)
    dependencies = extract_dependencies(pom_content)

    print("прямые зависимости:")
    for group_id, artifact_id, version in dependencies:
        full_name = f"{group_id}:{artifact_id}:{version}"
        if args.filter and args.filter not in full_name:
            continue
        print(full_name)

except ET.ParseError:
    print("файл pom содержит некорректный xml", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print(f"файл {args.url} не найден", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"oшибка при получении данных - {e}", file=sys.stderr)
    sys.exit(1)
